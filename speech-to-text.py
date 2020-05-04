from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import LanguageTranslatorV3

from moviepy.editor import *
from pydub.silence import split_on_silence, detect_nonsilent
from pydub import AudioSegment
import pandas as pd
import os
import shutil
from google.cloud import translate_v2 as translate



# 提取视频中的音频文件,audio 支持 ogg,mp3,wav,m4a,video 支持mp4，ogv,webm,avi,mov
def transfer_to_audio(movie, rewriteaudio):
    video = VideoFileClip(movie)
    audio = video.audio
    return audio.write_audiofile(rewriteaudio, bitrate='500k')


# 按停顿切分音频文件
def split_audio(filename, format):
    sound = AudioSegment.from_file(filename, format=format)
    dbfs = sound.dBFS
    chunks = split_on_silence(sound, min_silence_len=1000, silence_thresh=dbfs - 16, keep_silence=400)
    print("总分段：" + str(len(chunks)))
    return chunks


# 找到非静音的片段时间
def detect_nonsilence_audiotime(filename, format):
    sound = AudioSegment.from_file(filename, format=format)
    dbfs = sound.dBFS
    print("正在查找非静音片段，根据视频大小，等待时间会有不同～请耐心等待")
    timestamp_list = detect_nonsilent(sound, min_silence_len=700, silence_thresh=dbfs - 16, seek_step=1)
    print('恭喜你，已经完成' + "共找到" + str(len(timestamp_list)) + "段语音")
    return timestamp_list


# 设置好google 的身份认证与系统的代理，修改credentials的文件地址和代理地址
os.environ.setdefault(
    'GOOGLE_APPLICATION_CREDENTIALS',
    '/Users/lijiayu/Downloads/video translator-2de8ab711797.json'
)
os.environ.setdefault(
    'https_proxy',
    'http://127.0.0.1:41091'
)

# 授权获得speech-to-text的使用权限
speech_authenticator = IAMAuthenticator('yTFbV5j7yULHOZGU67UVS0vmCENKlIbQErZEl3TJPQFe')
speech_to_text = SpeechToTextV1(authenticator=speech_authenticator)
speech_to_text.set_service_url(
    'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/704f68a6-3924-4bd0-a760-3b03fd756b93')
translator_authenticator = IAMAuthenticator('8jUBnZk42eEFLmGumPk2LUfiWQrnrY8qibwouCT6ciLG')
language_translator = LanguageTranslatorV3(version='2020-04-20', authenticator=translator_authenticator)
language_translator.set_service_url(
    'https://api.eu-gb.language-translator.watson.cloud.ibm.com/instances/faf8761f-48a9-4bbe-9644-255b526d56a6')

# 授权获得google_translate的使用权限
client = translate.Client()

# class MyRecognizeCallback(RecognizeCallback):
#     def __init__(self):
#         RecognizeCallback.__init__(self)
#
#     def on_data(self, data):
#         print(json.dumps(data, indent=2))
#
#     def on_error(self, error):
#         print('Error received: {}'.format(error))
#
#     def on_inactivity_timeout(self, error):
#         print('Inactivity timeout: {}'.format(error))
#
# myRecognizeCallback = MyRecognizeCallback()

# audio_clip = AudioFileClip('test-video.mp3').subclip('00:2:40','00:03:20')
# audio_clip.write_audiofile('test-audio2.mp3',bitrate='500k')

# 自定义视频和转换的音频文件名称，修改videoname
videoname = 'ted-video'
rewriteaudio = videoname + '.wav'
transfer_to_audio(videoname + '.mp4', rewriteaudio)
sound = AudioSegment.from_file(videoname + '.wav', 'wav')
chunks = detect_nonsilence_audiotime(rewriteaudio, 'wav')
transcripts = []
translations = []

# 清除之前默认保存的音频文件
if os.path.exists('audio'):
    shutil.rmtree('audio')
os.mkdir('audio')

for i in range(len(chunks)):
    path = 'audio/%s%s.wav' % (videoname, i + 1)
    sound[chunks[i][0]:chunks[i][1]].export(path, format='wav')
    with open(path,
              'rb') as audio_file:
        print('====' * 10)
        print("正在翻译第" + str(i + 1) + "句,请稍后...")
        try:
            speech = speech_to_text.recognize(
                audio=audio_file,
                content_type='audio/wav',
                model='en-US_BroadbandModel', end_of_phrase_silence_time=0.8, smart_formatting=True,
                timestamps=True).get_result()
            timestamp_first = round(chunks[i][0] / 60000, 2)
            timestamp_last = round(chunks[i][1] / 60000, 2)
            translate_time = str(timestamp_first) + "min" + "------>" + str(timestamp_last) + "min"
            if len(speech['results']) > 1:
                transcript_to_concat = [speech['results'][i]['alternatives'][0]['transcript'] for i in
                                        range(len(speech['results']))]
                transcripts_finally = ','.join(transcript_to_concat)
                translation_resp = client.translate(transcripts_finally,
                                                    target_language='zh',
                                                    source_language='en',
                                                    model='nmt')
                if translation_resp is not None and 'translatedText' in translation_resp:
                    translation = translation_resp['translatedText']
                else:
                    print('没有找到可翻译的句子')
                    translation = None
                print(translate_time)
                print("原文是：" + str(transcripts_finally))
                print("翻译为：" + str(translation))
                transcripts.append(transcripts_finally)
                translations.append(translation)
            else:
                transcript = speech['results'][0]['alternatives'][0]['transcript']
                translation_resp = client.translate(
                    transcript,
                    target_language='zh',
                    source_language='en',
                    model='nmt'
                )
                if translation_resp is not None and 'translatedText' in translation_resp:
                    translation = translation_resp['translatedText']
                else:
                    print('没有找到可翻译的句子')
                    translation = None

                print(translate_time)
                print("原文是：" + str(transcript))
                print("翻译为：" + str(translation))
                transcripts.append(transcript)
                translations.append(translation)
        except Exception as e:
            print(e)
            pass

# 导出翻译的文本和原文
transcripts = "".join(transcripts)
translations = "".join(translations)
text_to_export = pd.DataFrame([transcripts,translations]).T
text_to_export.to_csv('text_to_export.csv')


if os.path.exists('audio'):
    shutil.rmtree('audio')
print('process complete!')
