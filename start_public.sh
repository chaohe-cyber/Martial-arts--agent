# 公网访问启动脚本 (Public Access)

echo "1. 正在启动 Web 界面 (后台运行)..."
# 启动 Streamlit 并放入后台，日志输出到 streamlit.log
export http_proxy= && export https_proxy= && export all_proxy= && nohup streamlit run src/interface/app.py --server.address 0.0.0.0 > streamlit.log 2>&1 &
STREAMLIT_PID=$!

echo "等待服务启动 (约5秒)..."
sleep 5

echo "-------------------------------------------------------"
echo "2. 正在创建公网链接 (使用 localhost.run 服务)..."
echo "请复制下方生成的 https://... 链接发给朋友"
echo "-------------------------------------------------------"
echo "注意: "
echo "1. 第一次运行可能需要输入 'yes' 确认指纹。"
echo "2. 保持此窗口开启，不要关闭。"
echo "3. 按 Ctrl+C 停止服务。"
echo "-------------------------------------------------------"

# 使用 SSH 端口转发将本地 8501 暴露到公网
# -R 80:localhost:8501 表示远程80端口转发到本地8501
# nokey@localhost.run 是免费服务账号
ssh -R 80:localhost:8501 nokey@localhost.run

# 当 ssh 结束后，杀掉后台的 streamlit 进程
kill $STREAMLIT_PID
