import React from 'react';
import ReactDOM from 'react-dom';

const updateIntervalInSeconds = 5;

function WorkerStatus(props) {
    return <p>Idle workers: {props.idle} / {props.total}</p>;
}

class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {}
    }

    componentDidMount() {
        console.log("ComponentDidMount");
        this.timerId = setInterval(
            () => this.tick(),
            updateIntervalInSeconds*1000
        );
        this.tick();
    }

    componentWillUnmount() {
        console.log("ComponentWillUnmount");
        clearInterval(this.timerId);
    }

    getJsonFromServer(callback) {
        const xhr = new XMLHttpRequest();
        xhr.open("get", "get_stats", true);
        xhr.onload = () => {
            const status = xhr.status;
            if (status == 200) {
                callback(xhr.response);
            } else {
                console.log("Got status " + status +
                            " from REST server.");
            }
        };
        xhr.send();
    }

    tick() {
        this.getJsonFromServer((response) => {
            console.log("json received: " + response);
            if (response !== null) {
                const data = JSON.parse(response);
                this.setState(data);
            }
        });
    }

    render() {
        return (
            <div>
                <WorkerStatus
                    idle={this.state.num_idle_workers}
                    total={this.state.num_total_workers} />
            </div>
        );
    }
}

ReactDOM.render(
    <App />,
    document.getElementById('root')
);
