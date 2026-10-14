FROM alpine:3.20
RUN apk add --no-cache ffmpeg
# Publishes a synthetic test stream (testsrc) to the MediaMTX path "cam1".
CMD ["sh", "-c", "ffmpeg -hide_banner -loglevel error -re -f lavfi -i testsrc=size=1280x720:rate=15 -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p -f rtsp rtsp://mediamtx:8554/cam1"]
