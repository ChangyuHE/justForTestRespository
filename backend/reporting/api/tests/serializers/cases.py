EXISTING_RELATIONS = [
    [
        {'name': 'item', 'args': 'test_msdk -s scenario_name -t case_1'},
        {'name': 'item', 'args': 'test_msdk -s scenario_name -t case_1', 'plugin_id': 1, 'scenario_id': 1, 'test_id': 'case_1'}
    ],
    [
        {'name': 'item', 'args': 'test_msdk      -s scenario_name -t case_1    '},
        {'name': 'item', 'args': 'test_msdk -s scenario_name -t case_1', 'plugin_id': 1, 'scenario_id': 1, 'test_id': 'case_1'}
    ],
    [
        {'name': 'item', 'args': 'test_msdk -s scenario_name'},
        {'name': 'item', 'args': 'test_msdk -s scenario_name', 'plugin_id': 1, 'scenario_id': 1, 'test_id': None}
    ],
    [
        {'name': 'item', 'args': '          test_msdk -t 123'},
        {'name': 'item', 'args': 'test_msdk -t 123', 'plugin_id': 1, 'scenario_id': None, 'test_id': '123'}
    ],
    [
        {'name': 'item', 'args': '-s scenario_name -t 1 foo bar bazzz'},
        {'name': 'item', 'args': '-s scenario_name -t 1 foo bar bazzz', 'plugin_id': None, 'scenario_id': 1, 'test_id': '1'}
    ],
    [
        {'name': 'item', 'args': ' -s scenario_name -t 1 foo bar bazzz'},
        {'name': 'item', 'args': '-s scenario_name -t 1 foo bar bazzz', 'plugin_id': None, 'scenario_id': 1, 'test_id': '1'}
    ],
    [
        {'name': 'item', 'args': 'something --flags "/@asdf er oojasdf" different from our format -h !sdf ###$'},
        {'name': 'item', 'args': 'something --flags "/@asdf er oojasdf" different from our format -h !sdf ###$',
         'plugin_id': None, 'scenario_id': None, 'test_id': None}
    ]
]

NEW_RELATIONS = [
    [
        {'name': 'item', 'args': 'something -s     new_scenario'},
        {'name': 'item', 'args': 'something -s new_scenario',
         'plugin_id': None, 'scenario__name': 'new_scenario', 'test_id': None}
    ],
    [
        {'name': 'item', 'args': 'test_new_plugin -s new_scenario'},
        {'name': 'item', 'args': 'test_new_plugin -s new_scenario',
         'plugin__name': 'test_new_plugin', 'scenario__name': 'new_scenario', 'test_id': None}
    ]
]
