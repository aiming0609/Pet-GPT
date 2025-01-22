from toolbox import update_ui
from toolbox import CatchException, report_execption, write_results_to_file

def 解析源代码新(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import os
    import copy
    from .crazy_utils import (
        request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency,
        request_gpt_model_in_new_thread_with_ui_alive
    )

    # 第一步：解析并概述每个源文件，多线程处理
    inputs_array = []
    inputs_show_user_array = []
    history_array = []
    sys_prompt_array = []

    assert len(file_manifest) <= 512, "源文件太多（超过512个），请自行拆分或修改此限制。"

    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
        prefix = "接下来请你逐文件分析下面的工程" if index == 0 else ""
        i_say = prefix + f'请对下面的程序文件做一个概述文件名是{os.path.relpath(fp, project_folder)}，文件代码是 ```{file_content}```'
        i_say_show_user = prefix + f'[{index}/{len(file_manifest)}] 请对下面的程序文件做一个概述: {os.path.abspath(fp)}'

        inputs_array.append(i_say)
        inputs_show_user_array.append(i_say_show_user)
        history_array.append([])
        sys_prompt_array.append("你是一个程序架构分析师，正在分析一个源代码项目。你的回答必须简单明了。")

    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        history_array=history_array,
        sys_prompt_array=sys_prompt_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        show_user_at_complete=True
    )

    # 写入文件、刷新UI
    report_part_1 = copy.deepcopy(gpt_response_collection)
    res = write_results_to_file(report_part_1)
    chatbot.append(("完成？", "逐个文件分析已完成。" + res + "\n\n正在开始汇总。"))
    yield from update_ui(chatbot=chatbot, history=report_part_1)

    # 第二步：分组汇总分析
    batchsize = 16
    report_part_2 = []
    previous_iteration_files = []
    last_iteration_result = ""

    while file_manifest:
        this_iteration_file_manifest = file_manifest[:batchsize]
        this_iteration_gpt_response_collection = gpt_response_collection[: batchsize * 2]
        file_rel_path = [os.path.relpath(fp, project_folder) for fp in this_iteration_file_manifest]

        for idx, _ in enumerate(this_iteration_gpt_response_collection):
            if idx % 2 == 0:
                this_iteration_gpt_response_collection[idx] = f"{file_rel_path[idx // 2]}"

        previous_iteration_files.extend(file_rel_path)
        previous_iteration_files_string = ", ".join(previous_iteration_files)
        current_iteration_focus = ", ".join(file_rel_path)

        i_say = (
            f"根据以上分析，对程序的整体功能和构架重新做出概括。"
            f"然后用一张markdown表格整理每个文件的功能（包括{previous_iteration_files_string}）。"
        )
        inputs_show_user = (
            f"根据以上分析，对程序的整体功能和构架重新做出概括，本组文件为 {current_iteration_focus} + 已汇总文件。"
        )

        this_iteration_history = copy.deepcopy(this_iteration_gpt_response_collection)
        this_iteration_history.append(last_iteration_result)

        result = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=i_say,
            inputs_show_user=inputs_show_user,
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history=this_iteration_history,
            sys_prompt="你是一个程序架构分析师，正在分析一个项目的源代码。"
        )

        report_part_2.extend([i_say, result])
        last_iteration_result = result

        file_manifest = file_manifest[batchsize:]
        gpt_response_collection = gpt_response_collection[batchsize * 2:]

    history_to_return = report_part_1 + report_part_2
    final_res = write_results_to_file(history_to_return)
    chatbot.append(("完成了吗？", final_res))
    yield from update_ui(chatbot=chatbot, history=history_to_return)

@CatchException
def 解析项目本身(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, web_port):
    import glob
    file_manifest = [
        f for f in glob.glob('./*.py')
        if ('test_project' not in f) and ('gpt_log' not in f)
    ] + [
        f for f in glob.glob('./crazy_functions/*.py')
        if ('test_project' not in f) and ('gpt_log' not in f)
    ] + [
        f for f in glob.glob('./request_llm/*.py')
        if ('test_project' not in f) and ('gpt_log' not in f)
    ]

    if not file_manifest:
        report_execption(chatbot, history, a=f"解析项目: {txt}", b=f"找不到任何python文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)
        return

    yield from 解析源代码新(
        file_manifest, './', llm_kwargs, plugin_kwargs, chatbot, history, system_prompt
    )
