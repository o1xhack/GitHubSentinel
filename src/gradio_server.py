# src/gradio_server.py

import gradio as gr
from datetime import datetime, timedelta

from config import Config
from github_client import GitHubClient
from report_generator import ReportGenerator
from llm import LLM
from subscription_manager import SubscriptionManager
from logger import LOG

# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)
llm = LLM()
report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)

def export_progress(repo, selection_type, days=None, since_date=None, until_date=None):
    try:
        if selection_type == "日期范围":
            since = datetime.strptime(since_date, "%Y-%m-%d").strftime("%Y-%m-%dT%H:%M:%SZ")
            until = datetime.strptime(until_date, "%Y-%m-%d").strftime("%Y-%m-%dT%H:%M:%SZ")
        else:  # 报告周期
            until = datetime.now()
            since = (until - timedelta(days=int(days))).strftime("%Y-%m-%dT%H:%M:%SZ")
            until = until.strftime("%Y-%m-%dT%H:%M:%SZ")

        raw_file_path = github_client.export_progress_by_date_range(repo, since, until)
        report, report_file_path = report_generator.generate_report_by_date_range(raw_file_path, int(days) if days else (datetime.strptime(until_date, "%Y-%m-%d") - datetime.strptime(since_date, "%Y-%m-%d")).days)
        return report, report_file_path
    except Exception as e:
        LOG.error(f"生成报告时发生错误: {str(e)}")
        return f"生成报告时发生错误: {str(e)}", None

def update_visibility(selection):
    if selection == "日期范围":
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

def update_subscriptions():
    choices = subscription_manager.list_subscriptions()
    return gr.update(choices=choices)

def add_subscription(new_repo):
    try:
        if new_repo:
            if new_repo in subscription_manager.list_subscriptions():
                LOG.info(f"订阅 {new_repo} 已存在")
                return (
                    f"订阅 {new_repo} 已存在", 
                    update_subscriptions(), 
                    new_repo, 
                    gr.update(value=f"订阅 {new_repo} 已存在", visible=True)
                )
            subscription_manager.add_subscription(new_repo)
            LOG.info(f"添加订阅: {new_repo}")
            return (
                f"添加订阅成功: {new_repo}", 
                update_subscriptions(), 
                "", 
                gr.update(value=f"成功添加订阅: {new_repo}", visible=True)
            )
        return (
            "请输入有效的仓库名称", 
            update_subscriptions(), 
            new_repo, 
            gr.update(value="请输入有效的仓库名称", visible=True)
        )
    except Exception as e:
        LOG.error(f"添加订阅时发生错误: {str(e)}")
        return (
            f"添加订阅失败: {str(e)}", 
            update_subscriptions(), 
            new_repo, 
            gr.update(value=f"添加订阅失败: {str(e)}", visible=True)
        )

def remove_subscription(repo):
    try:
        if repo:
            subscription_manager.remove_subscription(repo)
            LOG.info(f"删除订阅: {repo}")
            return (
                f"删除订阅成功: {repo}", 
                update_subscriptions(), 
                gr.update(value=f"成功删除订阅: {repo}", visible=True)
            )
        return (
            "请选择要删除的仓库", 
            update_subscriptions(), 
            gr.update(value="请选择要删除的仓库", visible=True)
        )
    except Exception as e:
        LOG.error(f"删除订阅时发生错误: {str(e)}")
        return (
            f"删除订阅失败: {str(e)}", 
            update_subscriptions(), 
            gr.update(value=f"删除订阅失败: {str(e)}", visible=True)
        )

# 创建Gradio界面
with gr.Blocks(title="GitHubSentinel") as demo:
    gr.Markdown("# GitHubSentinel")
    
    notification = gr.Markdown(visible=False)
    
    with gr.Row():
        with gr.Column(scale=2):
            repo_dropdown = gr.Dropdown(
                choices=subscription_manager.list_subscriptions(),
                label="订阅列表",
                info="已订阅GitHub项目"
            )
            selection_type = gr.Radio(["日期范围", "报告周期"], label="选择方式", value="报告周期")
            
            with gr.Group() as date_range_group:
                since_date = gr.Textbox(label="开始日期", value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"), placeholder="YYYY-MM-DD", visible=False)
                until_date = gr.Textbox(label="结束日期", value=datetime.now().strftime("%Y-%m-%d"), placeholder="YYYY-MM-DD", visible=False)
            
            with gr.Group() as period_group:
                days_slider = gr.Slider(minimum=1, maximum=30, value=7, step=1, label="报告周期", info="生成项目过去一段时间进展，单位：天")
            
            with gr.Row():
                clear_btn = gr.Button("Clear")
                submit_btn = gr.Button("Submit", variant="primary")

        with gr.Column(scale=2):
            output_markdown = gr.Markdown()
            output_file = gr.File(label="下载报告")

    with gr.Accordion("管理订阅", open=True) as subscription_accordion:
        new_repo_input = gr.Textbox(label="新增订阅", placeholder="输入GitHub仓库名 (例如: owner/repo)")
        add_btn = gr.Button("添加订阅")
        remove_btn = gr.Button("删除选中的订阅")
        subscription_msg = gr.Markdown()

    selection_type.change(
        update_visibility,
        inputs=[selection_type],
        outputs=[since_date, until_date, days_slider]
    )

    submit_btn.click(
        export_progress,
        inputs=[repo_dropdown, selection_type, days_slider, since_date, until_date],
        outputs=[output_markdown, output_file]
    )

    clear_btn.click(
        lambda: (None, None),
        outputs=[output_markdown, output_file]
    )

    add_btn.click(
        add_subscription,
        inputs=[new_repo_input],
        outputs=[subscription_msg, repo_dropdown, new_repo_input, notification]
    )

    remove_btn.click(
        remove_subscription,
        inputs=[repo_dropdown],
        outputs=[subscription_msg, repo_dropdown, notification]
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")