# 文本主要用到了ibm的语音转文本api和谷歌api

效果：视频语音转文本并自动翻译成中文，目前只支持英文视频转中文

使用方法：
1. 用户需要下载需要转文本并翻译的音频文件，不限制时长，和该代码文件默认存储在一个文件夹里
2. 设置好google 的身份认证与系统的代理，修改google credentials的文件地址和代理地址
3. 获取ibm的speechtotext的url地址和apikey，填在指定的位置
4. 修改videoname为你下载的视频名称
5. run
6. 默认会将文件保存为text_to_export.csv的文件

pip install google-cloud-storage
pip install google-cloud-translate==2.0.0



