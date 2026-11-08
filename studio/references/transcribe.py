import mlx_whisper,json,sys
d,lang=sys.argv[1],sys.argv[2]
r=mlx_whisper.transcribe(f'references/{d}/audio16k.wav',path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language=lang,word_timestamps=True)
json.dump(r,open(f'references/{d}/transcript.json','w'),ensure_ascii=False)
print(d,len(r['segments']))
