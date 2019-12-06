import time
from utils.utils import *
from utils.random_search import grid_choices_random
from utils.grid_search import grid_choices, get_num_grid_choices
from run_agent_parallel import train_PPO_agent, test_rule_based_agent, test_PPO_agent
import sys
import os
from data_collector import DataCollector, POSSIBLE_DATA


def run_grid_search(verbose, num_repeat_experiment, df_path=None, overwrite=True, data_to_collect=POSSIBLE_DATA,
                    MVP_key='waitingTime', save_model=True):
    grid = load_constants('constants/constants-grid.json')

    # Make the grid choice generator
    bases, num_choices = get_num_grid_choices(grid)
    grid_choice_gen = grid_choices(grid, bases)
    for diff_experiment, constants in enumerate(grid_choice_gen):
        data_collector_obj = DataCollector(data_to_collect, MVP_key, constants,
                                           'test' if constants['other_C']['rule_set'] else 'eval',
                                           df_path, overwrite if diff_experiment == 0 else False, verbose)

        for same_experiment in range(num_repeat_experiment):
            print(' --- Running experiment {}.{} / {}.{} --- '.format(diff_experiment+1, same_experiment+1,
                                                                      num_choices, num_repeat_experiment))
            if save_model: data_collector_obj.set_save_model_path(
                'models/saved_models/grid_{}-{}.pt'.format(diff_experiment + 1, same_experiment + 1))
            run_experiment(diff_experiment+1, same_experiment+1, constants, data_collector_obj)


def run_random_search(verbose, num_diff_experiments, num_repeat_experiment, allow_duplicates=False, df_path=None,
                      overwrite=True, data_to_collect=POSSIBLE_DATA, MVP_key='waitingTime', save_model=True):
    grid = load_constants('constants/constants-grid.json')

    if not allow_duplicates:
        _, num_choices = get_num_grid_choices(grid)
        assert num_diff_experiments <= num_choices, \
            'Allow duplicates is set to false, and num of diff experiments requested is too high ({} > {})'\
                .format(num_diff_experiments, num_choices)
    # Make grid choice generator
    grid_choice_gen = grid_choices_random(grid, num_diff_experiments)
    for diff_experiment, constants in enumerate(grid_choice_gen):
        data_collector_obj = DataCollector(data_to_collect, MVP_key, constants,
                                           'test' if constants['other_C']['rule_set'] else 'eval',
                                           df_path, overwrite if diff_experiment == 0 else False, verbose)

        for same_experiment in range(num_repeat_experiment):
            print(' --- Running experiment {}.{} / {}.{} --- '.format(diff_experiment+1, same_experiment+1,
                                                                      num_diff_experiments, num_repeat_experiment))
            if save_model: data_collector_obj.set_save_model_path('models/saved_models/random_{}-{}.pt'.
                                                                  format(diff_experiment+1, same_experiment+1))
            run_experiment(diff_experiment+1, same_experiment+1, constants, data_collector_obj)


def run_normal(verbose, num_experiments=1, df_path=None, overwrite=True, data_to_collect=POSSIBLE_DATA,
               MVP_key='waitingTime', save_model=True, load_model_file=None):
    # if loading, then dont save
    if load_model_file:
        save_model = False

    if not df_path:
        df_path = 'run-data.xlsx'  # def. path

    # Load constants
    constants = load_constants('constants/constants.json')
    episode_C, model_C, agent_C, other_C = constants['episode_C'], constants['model_C'], \
                                                   constants['agent_C'], constants['other_C']

    data_collector_obj = DataCollector(data_to_collect, MVP_key, constants,
                                       'test' if other_C['rule_set'] or load_model_file else 'eval',
                                       df_path, overwrite, verbose)

    loaded_model = None
    if load_model_file:
        loaded_model = torch.load('models/saved_models/' + load_model_file)

    for exp in range(num_experiments):
        print(' --- Running experiment {} / {} --- '.format(exp + 1, num_experiments))
        if save_model: data_collector_obj.set_save_model_path('models/saved_models/normal_{}.pt'.format(exp+1))
        run_experiment(exp+1, None, constants, data_collector_obj, loaded_model=loaded_model)


def run_experiment(exp1, exp2, constants, data_collector_obj, loaded_model=None):
    data_collector_obj.start_timer()

    if loaded_model:
        assert not constants['other_C']['rule_set']
        test_PPO_agent(constants, device, data_collector_obj, loaded_model)
    elif not constants['other_C']['rule_set']:
        train_PPO_agent(constants, device, data_collector_obj)
    else:
        test_rule_based_agent(constants, device, data_collector_obj)

    # Save and Refresh the data_collector
    data_collector_obj.end_timer(printIt=True)
    data_collector_obj.process_data()
    data_collector_obj.print_summary(exp1, exp2)
    data_collector_obj.done_with_experiment()


if __name__ == '__main__':
    # we need to import python modules from the $SUMO_HOME/tools directory
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    device = torch.device('cpu')

    # df_path = 'run-data.xlsx'

    # print('Num cores: {}'.format(mp.cpu_count()))

    run_normal(verbose=True, num_experiments=1, df_path='run-data.xlsx', overwrite=True,
               data_to_collect=POSSIBLE_DATA, MVP_key='waitingTime', save_model=True, load_model_file='normal_1.pt')

    # run_random_search(verbose=True, num_diff_experiments=2, num_repeat_experiment=1, allow_duplicates=False,
    #                   df_path='run-data.xlsx', overwrite=True, data_to_collect=POSSIBLE_DATA, MVP_key='waitingTime',
    #                   save_model=True)

    # run_grid_search(verbose=True, num_repeat_experiment=1, df_path='run-data.xlsx', overwrite=True,
    #                 data_to_collect=POSSIBLE_DATA, MVP_key='waitingTime', save_model=True)
