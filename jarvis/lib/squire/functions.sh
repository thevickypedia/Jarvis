os_agnostic() {
    echo -e '\n***************************************************************************************************'
    echo "                             Installing OS agnostic dependencies"
    echo -e '***************************************************************************************************\n'
    current_dir="$1"
    python -m pip install --no-cache-dir -r "$current_dir"/version_pinned_requirements.txt
    python -m pip install --no-cache-dir -r "$current_dir"/version_locked_requirements.txt
    python -m pip install --no-cache-dir --upgrade -r "$current_dir"/version_upgrade_requirements.txt
}

download_from_ext_sources_windows() {
    echo -e '\n***************************************************************************************************'
    echo "                             Installing externally sourced dependencies"
    echo -e '***************************************************************************************************\n'
    # Downloads ffmpeg for audio conversion when received voice commands from Telegram API
    curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-lgpl.zip --output ffmpeg.zip --silent
    unzip ffmpeg.zip && rm -rf ffmpeg.zip && mv ffmpeg-master-latest-win64-lgpl ffmpeg

    pyaudio="$1"
    # Downloads PyAudio's wheel file to install it on Windows
    curl https://vigneshrao.com/jarvis/"$pyaudio" --output "$pyaudio" --silent
    pip install "$pyaudio"
    rm "$pyaudio"
}
