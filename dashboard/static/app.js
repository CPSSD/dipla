import React from 'react';
import ReactDOM from 'react-dom';
import hrt from 'human-readable-time';
const DoughnutChart = require("react-chartjs-2").Doughnut;
const Chart = require("react-chartjs-2").Chart;

const updateIntervalInSeconds = 5;
Chart.defaults.global.defaultFontColor = '#fff';


function ResultsStatus(props) {
    return <p>The server has received {props.results + "\n"}
        computation results from clients.</p>;
}

function WorkerStatus(props) {
    return <p>Idle workers: {props.idle} / {props.total}</p>;
}

class WorkerChart extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        const chartData = {
                labels: ["Idle", "Busy"],
                datasets: [{
                    data: [this.props.idle,
                           this.props.total - this.props.idle],
                    backgroundColor: ["#77DD68", "#E85422"],
                    hoverBackgroundColor: ["#000", "#000"]
                }]
        };
        return <DoughnutChart
                    data={chartData}
                    width={500}
                    height={350}
                    id="workerchart"
                    options={{
                        responsive: false,
                        maintainAspectRatio: true,
                        scaleFontColor: "#FFF"
                    }} />;
    }
}

class RuntimeStatus extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            start_time: new Date() // ISO8601 in UTC
        };
    }

    componentDidMount() {
        this.timerId = setInterval(
            () => {
                const humanReadable = hrt(new Date(this.state.start_time),
                                          "%relative%");
                this.setState({
                    human_readable: humanReadable
                })
            },
            1000,
        );
    }

    componentWillUnmount() {
        clearInterval(this.timerId);
    }

    componentWillReceiveProps(nextProps) {
        this.setState({
            start_time: new Date(nextProps.start)
        });
    }

    render() {
        return (<p>Server started running {"\n"}
            {this.state.human_readable} ago.</p>);
    }
}

class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {}
    }

    componentDidMount() {
        this.timerId = setInterval(
            () => this.tick(),
            updateIntervalInSeconds*1000
        );
        this.tick();
    }

    componentWillUnmount() {
        clearInterval(this.timerId);
    }

    getJsonFromServer(callback) {
        const xhr = new XMLHttpRequest();
        xhr.open("get", "get_stats", true);
        xhr.onload = () => {
            const status = xhr.status;
            if (status == 200) {
                callback(xhr.response);
                this.setState({"rest_success": true});
            } else {
                console.log("Got status " + status +
                            " from REST server.");
                // server is up, but not serving at this endpoint
                this.setState({"rest_success": false});
            }
        };
        xhr.onerror = () => {
            // server is down
            this.setState({"rest_success": false});
        }
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
        console.log(this.state.start_time);
        return (
            <div>
                <WorkerChart
                    idle={this.state.num_idle_workers}
                    total={this.state.num_idle_workers} />
                <WorkerStatus
                    idle={this.state.num_idle_workers}
                    total={this.state.num_total_workers} />
                <ResultsStatus 
                    results={this.state.num_results_from_clients} />
                <RuntimeStatus start={this.state.start_time} />
                { (!this.state.rest_success) && (<h1>Could not connect</h1>) }
            </div>
        );
    }
}

ReactDOM.render(
    <App />,
    document.getElementById('root')
);
