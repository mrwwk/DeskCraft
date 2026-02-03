# install_taiji_client.sh
# taiji
wget http://jizhi.oa.com/taiji_client_golang/taiji_client -O /usr/bin/taiji_client
chmod +x /usr/bin/taiji_client
taiji_client update

#访问外网，可能需要配置代理
export http_proxy=http://hk-mmhttpproxy.woa.com:11113/ https_proxy=http://hk-mmhttpproxy.woa.com:11113/ no_proxy=localhost,28.33.*
#可以在这安装环境
