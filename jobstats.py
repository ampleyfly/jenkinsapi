import argparse
from jenkinsapi import jenkins
import pandas
import matplotlib.pyplot as plt


def get_build_times(api, job_name):
    api_data = api.get_json(jenkins.job_url(job_name) + '?depth=1&tree=allBuilds[timestamp,duration,builtOn,result]')

    # Partition builds by node, ignoring builds that did not succeed
    builds_by_node = {'All': []}
    for build in api_data['allBuilds']:
        if build['result'] != 'SUCCESS':
            continue
        node = build['builtOn']
        if node not in builds_by_node:
            builds_by_node[node] = []
        builds_by_node[node].append(build)
        builds_by_node['All'].append(build)

    sorted_nodes = sorted(builds_by_node.keys())

    # Create a time series for each node
    time_series = dict()
    for node in sorted_nodes:
        builds = builds_by_node[node]
        durations = [int(b['duration'])/60000 for b in builds]
        timestamps = pandas.to_datetime([int(b['timestamp']) for b in builds], unit='ms')
        time_series[node] = pandas.Series(data=durations, index=timestamps)

    return time_series


def print_build_times(time_series):
    sorted_nodes = sorted(time_series.keys())
    nodewidth = max(len(n) for n in sorted_nodes)
    print('{:{}}\t{:15}\t{:16}'.format('Node', nodewidth, 'Mean build time', 'Number of builds'))
    for node in sorted_nodes:
        print('{:{}}\t{:15.2f}\t{:16}'.format(node, nodewidth, time_series[node].mean(), len(time_series[node])))


def plot_build_times(time_series, filter_func):
    sorted_nodes = sorted(time_series.keys())
    plt.figure()
    ax = None
    colors = ['red', 'cyan', 'blue', 'lightblue', 'purple', 'brown', 'lime', 'magenta', 'orange', 'olivedrab']
    for i, node in enumerate(sorted_nodes):
        series = filter_func(time_series[node])
        color = colors[i % len(colors)]
        if ax is None:
            ax = series.plot(label=node, figsize=(20, 10), color=color, linewidth=2)
        else:
            series.plot(label=node, ax=ax, color=color, linewidth=2)

    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    # Put a legend to the right of the current axis
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))


def filter_id(series):
    return series


def filter_pad(series):
    return series.resample('min', fill_method='pad')


def filter_mean(window, freq):
    def doit(series):
        return pandas.rolling_mean(series.resample('min', fill_method='pad'), window=window, freq=freq, center=True)
    return doit


if __name__ == '__main__':
    config = jenkins.read_api_config()
    parser = argparse.ArgumentParser()
    parser.add_argument('job_name')
    parser.add_argument('--user', default=config.get('auth', 'user'))
    parser.add_argument('--token', default=config.get('auth', 'token'))
    parser.add_argument('--url', default=config.get('jenkins', 'url'))
    args = parser.parse_args()
    api = jenkins.JenkinsApi(args.url, args.user, args.token)
    build_times = get_build_times(api, args.job_name)
    print_build_times(build_times)
