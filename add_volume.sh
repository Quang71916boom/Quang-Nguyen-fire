sed -i '/<div id="yt-player"/i\
                                    <div class="flex items-center gap-3 w-full px-4 mt-2">\
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>\
                                        <input type="range" id="music-volume" min="0" max="100" value="50" class="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500">\
                                    </div>' index.html

sed -i '/function onPlayerReady(event) {/a\
            ytPlayer.setVolume(document.getElementById("music-volume").value);' index.html

sed -i '/<\/script>/i\
        document.getElementById("music-volume").addEventListener("input", (e) => {\
            if (ytPlayer && ytPlayer.setVolume) {\
                ytPlayer.setVolume(e.target.value);\
            }\
        });' index.html
