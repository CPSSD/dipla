import React from 'react';
import ReactDOM from 'react-dom';

const updateIntervalInSeconds = 10;

function WorkerStatus(props) {
    return <p>Idle workers: {props.idle} / {props.total}</p>;
}

function App(props) {
    return (
        <div>
            <WorkerStatus />
        </div>
    );
}

function tick() {
    console.log("HI there");
    ReactDOM.render(
        <App />,
        document.getElementById('root')
    );
}

tick();
setInterval(tick, updateIntervalInSeconds*1000);
