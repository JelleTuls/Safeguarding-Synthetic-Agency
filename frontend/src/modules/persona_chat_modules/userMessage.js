import './userMessage.css';
import MessageAnalysis from './messageAnalysis';

function UserMessage({text, analysis}) {

  return (
    <div className="UserMessage">
        <div>
          <MessageAnalysis analysis={analysis} align="right" />
          <p className="unbounded-weight300">{text}</p>
          <div id="user-message-bubbletick"></div>
        </div>
    </div>
  );
};

export default UserMessage;
