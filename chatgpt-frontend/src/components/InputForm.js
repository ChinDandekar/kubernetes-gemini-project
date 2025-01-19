import React from 'react';
import '../assets/InputForm.css';
import ExpandingTextarea from './ExpandingTextArea';

const InputForm = ({ onSendMessage }) => {

  const handleSubmit = (text) => {
    if (text.trim()) {
      onSendMessage(text);
    }
  };

  return (
    <form className="input-form" onSubmit={handleSubmit}>
       <ExpandingTextarea onSubmit={handleSubmit} />
      <button type="submit">Send</button>
    </form>
  );
};

export default InputForm;
