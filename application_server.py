from socket import *
import threading
import time
import sys
import argparse
import pickle
from collections import deque
import select
import google.generativeai as genai
from dotenv import load_dotenv
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()
load_dotenv()
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# Application vars
isFailure = threading.Event()
context_dict = {} # stores context for each context id
context_dict_lock = threading.Lock()
answers_dict = {} # stores answers 1, 2 and 3 for user to choose from, based on the context_id
answers_dict_lock = threading.Lock()

SERVER_ID = 0
NETWORK_PORT = 9000
TIMEOUT = 15
LEADER_PID = 0
leader_lock = threading.Lock()
updated_dict_flag = threading.Event()

print_lock = threading.Lock()
app_network_socket = None
read_lock = threading.Lock()
client_operation_queue = deque([])
client_operation_queue_lock = threading.Lock()
network_send_lock = threading.Lock()

ack_dict = {}
ack_dict_lock = threading.Lock()

# leader election vars
ballotNum = (0,0,0)
ballotNum_lock = threading.Lock()
promise_count = 0
promise_count_lock = threading.Lock()
leader_operation_queue = deque([])
leader_operation_queue_lock = threading.Lock()
election_flag = threading.Event()

# Paxos vars
op_num = 0
op_num_lock = threading.Lock()
seq_num = 0
seq_num_lock = threading.Lock()
acceptNum = (0,0,0)
acceptVal = None
accept_locks = threading.Lock()

accept_count = 0
accept_count_lock = threading.Lock()
accepted_flag = threading.Event()


def listen_to_nw_server():
    global context_dict
    global op_num
    global ballotNum
    data = 0
    counter = 0
    while True:
        try:
            while not data:
                data = app_network_socket.recv(70000)
            data = pickle.loads(data)  
            # if client wants to close connection, break out of while loops
            if type(data) == str:
                print(f"recieved: {data}")
                if data == 'q':
                    break
            else:
                # prepare in election, sent by wannabe leader
                if data[0] == 'prepare':
                    recv_prepare(data)
                # promise in election, sent by acceptor
                elif data[0] == 'promise':
                    recv_promise(data)
                    
                # ACK in replication, leader has added operation to queue
                elif data[0] == 'ACK':
                    with ack_dict_lock:
                        if (data[1], data[2], data[3]) in ack_dict and type(ack_dict[(data[1], data[2], data[3])]) == bool and not ack_dict[(data[1], data[2], data[3])]:
                            ack_dict[(data[1], data[2], data[3])] = True
                            with client_operation_queue_lock:
                                deque.popleft(client_operation_queue)
                            print_update("ACK")
                        else:
                            ack_dict[(data[1], data[2], data[3])].set()
                        
                # Accept in replication, sent by leader
                elif data[0] == 'accept':
                    recv_accept(data)
                # Accepted in replication, sent by acceptors
                elif data[0] == 'accepted':
                    recv_accepted(data)
                # Decide in replication, sent by leader, commit operations
                elif data[0] == 'decide':
                    decide_thread = threading.Thread(target=recv_decide, args=(data,))
                    decide_thread.daemon = True
                    decide_thread.start()
                # Append in replication, leader appends operation to queue
                elif data[0] == 'append':
                    append_leader_queue(data)
                # display llm response for user on terminal it requested 
                elif data[0] == 'answer':
                    display_llm_response(data)
                elif data[0] == 'recover':
                    if LEADER_PID == SERVER_ID:
                        loop_in_node(data)
                        # src = data[1]
                        # temp = ("update_dict", ballotNum, context_dict, SERVER_ID, src)
                        # send_network(temp)
                elif data[0] == 'update_dict':
                    update_status(data)
                    # _, recv_ballotNum, context_dict, src, _ = data
                    # print_update("RECOVERY", content=src)
                    # with op_num_lock:
                    #     op_num = recv_ballotNum[0]
                    # with ballotNum_lock:
                    #     ballotNum = recv_ballotNum
                    # updated_dict_flag.set()
                elif data[0] == 'status':
                    loop_in_node(data)
                elif data[0] == 'recovery2':
                    update_status(data)
                
                elif data[0] == "die":
                    os._exit(0)
            data = None
            counter += 1
        except ConnectionError:
            break
    
    print("Stopped listening to nw")
    
def set_and_send_to_leader(leader):
    global LEADER_PID
    global client_operation_queue
    global leader_operation_queue
    with leader_lock:
        LEADER_PID = leader
    
    if LEADER_PID == SERVER_ID:
        repl_thread = threading.Thread(target=replication_phase, args=())
        repl_thread.daemon = True
        repl_thread.start()
    else:
        # with client_operation_queue_lock:
        #     for operation, context_id, params, _ in client_operation_queue:
        #         start_operation(operation, context_id, params)

        # with leader_operation_queue_lock:
        #     with client_operation_queue_lock:
        #         for operation, context_id, params, _ in leader_operation_queue:
        #             deque.append(client_operation_queue, [operation, context_id, params])
        #             start_operation(operation, context_id, params)
        
        if LEADER_PID:
            with leader_operation_queue_lock:
                with client_operation_queue_lock:
                    if len(leader_operation_queue):
                        client_operation_queue = leader_operation_queue + client_operation_queue
                        leader_operation_queue.clear()
            
            with client_operation_queue_lock:
                for operation, context_id, params, _ in client_operation_queue:
                    # first SERVER_ID is the original source
                    data = ('append', operation, context_id, params, SERVER_ID, SERVER_ID, LEADER_PID)
                    with ack_dict_lock:
                        if ((operation, context_id, params)) in ack_dict:
                            ack_dict[((operation, context_id, params))] = False
                    send_network(data)

    

def update_status(data):
    global ballotNum
    global op_num
    global context_dict
    #  global LEADER_PID
    _, recv_ballotNum, leader_id, recv_context_dict, src, _ = data
    with ballotNum_lock:
        if recv_ballotNum > ballotNum:
            ballotNum = recv_ballotNum
            with op_num_lock:
                op_num = recv_ballotNum[0]
            
            set_leader_thread = threading.Thread(target=set_and_send_to_leader, args=(leader_id,))
            set_leader_thread.daemon = True
            set_leader_thread.start()
            with context_dict_lock:
                context_dict = recv_context_dict
            if data[0] == "update_dict":
                updated_dict_flag.set()
            print_update("RECOVERY", content=src)

def loop_in_node(data):
    global ballotNum
    global op_num
    _, recv_ballotNum, src, _ = data
    with ballotNum_lock:
        with op_num_lock:
            if ballotNum > recv_ballotNum or op_num > recv_ballotNum[2]:
                with context_dict_lock:
                    if data[0] == "recover":
                        data = ("update_dict", ballotNum, LEADER_PID, context_dict, SERVER_ID, src)
                    else:
                        data = ("recovery2", ballotNum, LEADER_PID, context_dict, SERVER_ID, src)
                    send_network(data)
# llm methods

def display_llm_response(data):
    answer, context_id, response, src, dest = data
    print_markdown(f"Choice {src}", "magenta", response)
    with answers_dict_lock:
        answers_dict[(context_id, f"{src}")] = response
 
# replication phase methods
 
def append_leader_queue(data):
    _, operation, context_id, params, og_src, src, _ = data
    with leader_lock:
        if LEADER_PID != SERVER_ID:
            # i'm not leaader but i'll send it to who i think is known leader
            if LEADER_PID:
                # now forward append
                new_data = ('append', operation, context_id, params, og_src, LEADER_PID, src)
                print_update("FORWARD", content=f"{operation} to server {LEADER_PID}")
                send_network(new_data)
            return
    
    with leader_operation_queue_lock:
        leader_operation_queue.append((operation, context_id, params, og_src))
    
    # sending ack
    if src == SERVER_ID:
        with ack_dict_lock:
            if ((operation, context_id, params)) in ack_dict:
                ack_dict[(operation, context_id, params)].set()
    else:
        data = ('ACK', operation, context_id, params, SERVER_ID, og_src)
        time.sleep(0.5)
        send_network(data)

def replication_phase():
    # add our acceptVal onto our leader queue
    global acceptVal
    if acceptVal:
        with leader_operation_queue_lock:
            leader_operation_queue.append((acceptVal[0], acceptVal[1], acceptVal[2], SERVER_ID))
        with accept_locks:
            acceptVal = None

    # constantly checking leader queue for new operations to execute
    for item in client_operation_queue:
        with leader_operation_queue_lock:
            leader_operation_queue.append(item)
    
    with client_operation_queue_lock:
        client_operation_queue.clear()
    # start executing operations
    global op_num
    global accept_count
    global LEADER_PID
    while SERVER_ID == LEADER_PID:
        if len(leader_operation_queue) > 0:
            # remove from queue of operations
            
            operation, context_id, params, src = leader_operation_queue[0]
              
            # send accepts
            broadcast_accept(operation, context_id, params)
            majority_accepted = accepted_flag.wait(TIMEOUT)
            # with accept_count_lock:            
            #     if accept_count == 2:
            #         accepted_flag.set()
            
            if majority_accepted:
                # send decides
                broadcast_decide_and_execute(operation, context_id, params)
                with leader_operation_queue_lock:
                    operation, context_id, params, src = deque.popleft(leader_operation_queue)

            else: # leader did not receive majority of accepted, must realize it is not leader anymore
                LEADER_PID = None
                print_update("TIMEOUT", content=f"did not recieve majority of accepted, only recieved {accept_count} accepted")
                start_election()
                break
        else:     
            continue

def broadcast_decide_and_execute(operation, context_id, params):
    global ballotNum
    global acceptNum
    for i in range(1,4):
        data = ("decide", operation, ballotNum, context_id, params, SERVER_ID, i)
        # operation, op_num, src, dest
        if i != SERVER_ID:  
            send_network(data)
            log_paxos_message("sent DECIDE", acceptNum, dest=i, data=data)

    recv_decide(data)
    
    
def broadcast_accept(operation, context_id, params):
    global op_num
    global accept_count
    global ballotNum
    global acceptNum
    global acceptVal

    # broadcast accepts to all clients
    with accept_count_lock:
        accept_count = 0
        accepted_flag.clear()
    
    with accept_locks:
        acceptNum = (op_num, ballotNum[1], ballotNum[2])
        acceptVal = (operation, context_id, params)
        accept_count += 1     
        
    for i in range(1,4):
        if i != SERVER_ID:
            # operation, op_num, src, dest
            data = ("accept", acceptNum, operation, context_id, params, SERVER_ID, i)
            send_network(data)
            log_paxos_message("sent ACCEPT", acceptNum, dest=i, data=data)

def recv_accept(data):
    global op_num
    global ballotNum
    global acceptNum
    global acceptVal
    operation, rcv_ballotNum, operation, context_id, params, src, dest = data
    log_paxos_message("received ACCEPT", rcv_ballotNum, src=src, data=data)
    if ballotNum <=  rcv_ballotNum:
        # then update my acceptVal and acceptNum before sending accepted
        acceptNum = rcv_ballotNum
        acceptVal = (operation, context_id, params)
        # accepted
        send_data = ('accepted', rcv_ballotNum, SERVER_ID, src)
        send_network(send_data)
        log_paxos_message("sent ACCEPTED", rcv_ballotNum, dest=src, data=data)
    # else don't respond

def recv_accepted(data):
    global op_num
    global accept_count    
    global ballotNum
    operation, recv_ballotNum, src, dest = data
    log_paxos_message("received ACCEPTED", recv_ballotNum, src=src, data=data)

    if LEADER_PID == SERVER_ID:
        if recv_ballotNum[0] == op_num:
            with accept_count_lock:
                accept_count += 1
                # accepted_flag.set()

    with accept_count_lock:            
        if accept_count == 2:
            accepted_flag.set()


def recv_decide(data):
    global op_num
    global ballotNum
    global acceptNum
    global acceptVal
    global LEADER_PID

    decide, operation, recv_ballotNum, context_id, params, src, dest = data
    # in case we just recovered after crash, we want current context before we add new operation
    with op_num_lock:
        isProcBehind = op_num < recv_ballotNum[0]
    if isProcBehind:
        # catch me up leader because I just recovered
        # with ballotNum_lock:
        #     data = ('status', ballotNum, SERVER_ID, src)
        # send_network(data)

        recovery_data = ("recover", ballotNum, SERVER_ID, src)
        send_network(recovery_data)
        while not updated_dict_flag.is_set():
            continue
        updated_dict_flag.clear()
        with op_num_lock:
            isBehind = op_num == recv_ballotNum[0]
            
        # leader hasn't already commited operation
        if isBehind:
            commit_operation(data, operation, recv_ballotNum, context_id, params, src)
        else:
            if operation == "query":
                _, src_of_req = params
                query = context_dict[context_id]
                query_llm(context_id, src_of_req, query)
            else:
                print_update("ALREADY COMMITTED")

    
    else:
        commit_operation(data, operation, recv_ballotNum, context_id, params, src)

def commit_operation(data, operation, recv_ballotNum, context_id, params, src):
    global op_num
    global ballotNum
    global acceptNum
    global acceptVal
    with op_num_lock:
        op_num += 1
        with ballotNum_lock:
            ballotNum = (op_num, ballotNum[1], ballotNum[2])
    if src != SERVER_ID:
        log_paxos_message("received DECIDE", recv_ballotNum, src=src, data=data)
    else:
        log_paxos_message("commit OPERATION", recv_ballotNum, src=src, data=data)

    if operation == "create":
        create(context_id)
    elif operation == "query":
        query(context_id, params, src)
    elif operation == "choose":
        finish_choose(context_id, params)
    
    # reset acceptVal
    with accept_locks:
        acceptNum = (0,0,0)
        acceptVal = None
# execution methods
def create(context_id):
    with context_dict_lock:
        context_dict[context_id] = ''
    print_update("NEW CONTEXT", context_id=context_id)

def query(context_id, params, src):
    if context_id not in context_dict: 
        print(f"Conversation {context_id} does not exist. Please try again with a valid conversations. To see all conversations, execute the viewall command")
        return
    query_string, src_of_request = params
    
    
    query = context_dict[context_id] + f"**Query**: {query_string}\n"
    with context_dict_lock:
        context_dict[context_id] = query
    
     
    query_llm(context_id, src_of_request, query)

def query_llm(context_id, src_of_request, query):
    prompt = query + "\n**Answer**:"
    response = model.generate_content(prompt)
    with context_dict_lock:
        print_update("NEW QUERY", context_id=context_id, content=context_dict[context_id])

    if src_of_request == SERVER_ID:
        print_markdown(f"Choice: {SERVER_ID}", "magenta", response.text)
        with answers_dict_lock:
            answers_dict[(context_id, f"{SERVER_ID}")] = response.text
    else:
        # send to original requester server
        data = ("answer", context_id, response.text, SERVER_ID, src_of_request)
        send_network(data)

        
def start_choose(context_id, choice):
    chosen_answer = None
    with answers_dict_lock:
        if (context_id, choice) in answers_dict:
            chosen_answer = answers_dict[(context_id, choice)]
        else:
            print(f"{(context_id, choice)} not in answers_dict, content: {answers_dict}")
            
    if chosen_answer:
         # add to local queue
        with client_operation_queue_lock:
            deque.append(client_operation_queue, ("choose", context_id, chosen_answer, SERVER_ID))
        t = threading.Thread(target=start_operation, args=("choose", context_id, chosen_answer))
        t.daemon = True
        t.start()

def finish_choose(context_id, chosen_answer):
    with context_dict_lock:
        cur_context = context_dict[context_id]
        cur_context += "\n**Answer**: " + chosen_answer + "\n"
        context_dict[context_id] = cur_context
        print_update("CHOSEN ANSWER", context_id=context_id, content=context_dict[context_id])


def viewall():
    with context_dict_lock:
        if len(context_dict):
            for key, value in context_dict.items():
                print_markdown(f"Conversation {key}", "cyan", value)
        else:
            print("Context dictionary empty")

def print_markdown(title_text, color, context):
    title = Text(title_text, style="bold magenta")
    content = Markdown(context)
    panel = Panel(content, title=title, expand=False, border_style=color)
    console.print(panel)
    console.print()
    

def log_paxos_message(operation, ballotNum, src=None, dest=None, data=None):    
    if data and len(str(data)) > 50:
        data = f"{str(data)[:50]}..."
    else:
        data = str(data)

    border_colors = {
        "PREPARE": "green",
        "PROMISE": "yellow",
        "ACCEPT": "blue",
        "ACCEPTED": "red",
        "DECIDE": "purple",
        "OPERATION": "purple",
    }

    # Determine the border color based on the operation
    border_color = next((color for key, color in border_colors.items() if key in operation), "white")

    title = Text(f"PAXOS: {operation}", style=f"bold {border_color}")
    content = []

    content.append(Text(f"Ballot: ", style="bold green") + Text(str(ballotNum)))
    
    if src:
        content.append(Text(f"From: ", style="bold yellow") + Text(str(src)))
    if dest:
        content.append(Text(f"To: ", style="bold yellow") + Text(str(dest)))
    if data:
        content.append(Text(f"Data: ", style="bold magenta") + Text(data))

    message = "\n".join(str(line) for line in content)
    panel = Panel(message, title=title, expand=False, border_style=f"{border_color}")
    console.print(panel)
    
def print_update(update_type, context_id=None, content=None):
    title = Text("UPDATE", style="bold light green")
    
    if update_type == "NEW CONTEXT":
        message = f"NEW CONTEXT {context_id}"
    elif update_type == "NEW QUERY":
        content = content.replace('\n', '\n\n')
        message = f"NEW QUERY on {context_id} with:\n\n{content}"
        message = message[:200] + ' \n**...**\n ' + message[-200:] if len(message) > 450 else message
        message = Markdown(message)
        
    elif update_type == "CHOSEN ANSWER":
        content = content.replace('\n', '\n\n')
        message = f"CHOSEN ANSWER on {context_id} with:\n\n{content}"
        message = message[:200] + ' \n**...**\n ' + message[-200:] if len(message) > 450 else message
        message = Markdown(message)
        
    elif update_type == "ACK":
        message = "ACK"
    elif update_type == "TIMEOUT":
        message = "TIMEOUT " + content
    elif update_type == "RECOVERY":
        message = "RECOVERED DICTIONARY FROM SERVER " + str(content)
    elif update_type == "ALREADY COMMITTED":
        message = "OPERATION ALREADY COMMITTED BY LEADER"
    elif update_type == "FORWARD":
        message = "FORWARDED OPERATION to " + str(content)
    else:
        message = "Unknown update type"

    panel = Panel(message, title=title, expand=False, border_style="light_green")
    console.print(panel)
# leader election phase methods


def start_election():
    global seq_num
    global promise_count
    global ballotNum
    global op_num
    with seq_num_lock:
        seq_num = ballotNum[1]
        seq_num += 1
    with promise_count_lock:
        promise_count = 0
        election_flag.clear()
    #send PREPARE
    for i in range(1,4):
        if i != SERVER_ID:
            # operation, ballot, src, dest
            data = ("prepare", (op_num, seq_num, SERVER_ID), SERVER_ID, i)
            send_network(data)
            log_paxos_message("sent PREPARE", (op_num, seq_num, SERVER_ID), dest=i, data=data)
    
    # doing protocol on ourself -- check before promising
    with ballotNum_lock:
        if ballotNum < (op_num, seq_num, SERVER_ID):
            ballotNum = (op_num, seq_num, SERVER_ID)
            with promise_count_lock:
                promise_count += 1
    
    became_leader = election_flag.wait(TIMEOUT)
    if not became_leader:
        print_update("TIMEOUT", content="Leader election failed")

def recv_prepare(data):
    global ballotNum
    global acceptNum
    global acceptVal
    global seq_num
    global LEADER_PID
    operation, recv_ballotNum, src, dest = data
    log_paxos_message("received PREPARE", recv_ballotNum, src=src, data=data)
                                        # recv_ballotNum[2] is the recieved op_num
    if ballotNum < recv_ballotNum:
        # promise server to not respond to anything lower
        with seq_num_lock:
            seq_num = recv_ballotNum[1]
        
        with ballotNum_lock:
            ballotNum = recv_ballotNum
            # operation, ballotNum, acceptNum, acceptVal
            data = ('promise', ballotNum, acceptNum, acceptVal, SERVER_ID, src)
            send_network(data)
            log_paxos_message("sent PROMISE", ballotNum, dest=src, data=data)
            # send all the items in queue and update leader id
            
            set_leader_thread = threading.Thread(target=set_and_send_to_leader, args=(src,))
            set_leader_thread.daemon = True
            set_leader_thread.start()          
    else: # received lower ballotNum tell process to recover and catch up with system
        with context_dict_lock:
            data = ("recovery2", ballotNum, LEADER_PID, context_dict, SERVER_ID, src)
            send_network(data)

def recv_promise(data):
    global promise_count
    global ballotNum
    global LEADER_PID
    global acceptVal
    global acceptNum
    operation,recv_ballotNum, recv_acceptNum, recv_acceptVal, src, dest = data

    log_paxos_message("received PROMISE", recv_ballotNum, src=src, data=data)
    if recv_ballotNum == ballotNum:
        with promise_count_lock:
            promise_count += 1
        
    if recv_acceptVal:
        if recv_acceptNum >= acceptNum:
            with accept_locks:
                acceptVal = recv_acceptVal
                acceptNum = recv_acceptNum

    # received majority
    if promise_count == 2: # let's see if this is a problem later
        with leader_lock:
            LEADER_PID = SERVER_ID
            election_flag.set()

        t = threading.Thread(target=replication_phase, args=())
        t.daemon = True
        t.start()

def send_network(data):
    time.sleep(0.5)
    pickled_data = pickle.dumps(data)
    with network_send_lock:
        app_network_socket.sendall(pickled_data)

def broadcast_status():
    for i in range(1,4):
        if i != SERVER_ID:
            with ballotNum_lock:
                data = ('status', ballotNum, SERVER_ID, i)
            send_network(data)

def start_server():
    global SERVER_ID
    global app_network_socket
    global ballotNum
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help="client id", type=int)
    args = parser.parse_args()
    SERVER_ID = args.id

    # connect application server to network server
    app_network_socket = socket(AF_INET, SOCK_STREAM) # Create a TCP socket
    app_network_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    app_network_socket.connect(("", NETWORK_PORT))
    app_network_socket.sendall(pickle.dumps(SERVER_ID))
    
    # # thread to listen to network server
    listening = threading.Thread(target=listen_to_nw_server, args=())
    listening.daemon = True
    listening.start()

    # status check with other servers
    broadcast_status()

    while True:
        user_input = input()
        arr = user_input.split()
        if "create" in user_input:
            context_id = arr[1]
             # add to local queue
            with client_operation_queue_lock:
                deque.append(client_operation_queue, ("create", context_id, None, SERVER_ID))
            t = threading.Thread(target=start_operation, args=("create", context_id, None))
            t.daemon = True
            t.start()
        elif "query" in user_input:
            context_id = arr[1]
            query_string = arr[2:]
            query_string = ' '.join(word for word in query_string)
            params = (query_string, SERVER_ID)
             # add to local queue
            with client_operation_queue_lock:
                deque.append(client_operation_queue, ("query", context_id, params, SERVER_ID))
            t = threading.Thread(target=start_operation, args=("query", context_id, params))
            t.daemon = True
            t.start()
        elif "choose" in user_input:
            context_id = arr[1]
            choice = arr[2]
            start_choose(context_id, choice)
        elif user_input == "viewall":
            viewall()
        elif "view" in user_input:
            context_id = arr[1]
            with context_dict_lock:
                if context_id in context_dict:
                    print_markdown(f"Conversation {context_id}", "cyan", context_dict[context_id])
                else:
                    print(f"Requested context_id {context_id} has not been created")
        elif "failLink" in user_input:
            src = arr[1]
            dest = arr[2]
            data = ("failLink", src, dest)     
            send_network(data)
        elif "fixLink" in user_input:
            src = arr[1]
            dest = arr[2]
            data = ("fixLink", src, dest)
            send_network(data)
        elif "failNode" in user_input:
            node = arr[1]
            data = ("die", SERVER_ID, node)
            send_network(data)
            if int(node) == SERVER_ID:
                sys.exit()
        elif user_input == 'ballotNum':
            print(f"BallotNum: {ballotNum}")
        elif user_input == 'queue':
            print(f"leader_operation_queue: {leader_operation_queue}")
            print(f"client_operation_queue: {client_operation_queue}")
        elif user_input == "q":
            sys.exit()


def start_operation(operation, context_id, params = None):
    
    with ack_dict_lock:
        ack_dict[(operation, context_id, params)] = threading.Event()        
    cur_flag = ack_dict[(operation, context_id, params)]
    
    # check for leader/ start election
    if LEADER_PID:
        # send operation to leader
        # first SERVER_ID is the original source
        data = ('append', operation, context_id, params, SERVER_ID, SERVER_ID, LEADER_PID)
        if LEADER_PID == SERVER_ID:
            append_leader_queue(data)
        else:
            send_network(data)
        # wait for reply
        recvd_ack = cur_flag.wait(TIMEOUT)
        if recvd_ack:
            # else, remove from queue
            with client_operation_queue_lock:
                client_operation_queue.remove((operation, context_id, params, SERVER_ID)) 
            print_update("ACK")
        else:
            # if timeout, start election
            print_update("TIMEOUT", content = "did not receive ack from leader")
            start_election()
    else:
        start_election()

if __name__ == "__main__":
    start_server()