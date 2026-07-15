sed -i '1050,1101c\
                        <!-- TAB X: Music Player Panel -->\
                        <div id="panel-music" class="tab-panel hidden flex flex-col gap-6">\
                            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gradient-to-r from-purple-950/40 to-slate-900/60 border border-purple-500/10 p-5 rounded-2xl">\
                                <div>\
                                    <h3 class="text-lg font-medium text-white mb-1">🎵 Background Music</h3>\
                                    <p class="text-xs text-gray-400">Set the perfect mood for your chess matches</p>\
                                </div>\
                            </div>\
                            <div class="flex justify-center">\
                                <div class="bg-[#191D26] border border-[#2D3343] rounded-3xl p-6 w-full max-w-md flex flex-col gap-6 items-center shadow-2xl">\
                                    <div id="music-icon" class="w-32 h-32 rounded-full bg-slate-800 flex items-center justify-center text-6xl shadow-inner border-[4px] border-slate-700 transition-all duration-500">\
                                        🎸\
                                    </div>\
                                    <div class="text-center">\
                                        <h4 id="music-title" class="text-white text-xl font-bold">Metallica Riffs</h4>\
                                        <p id="music-desc" class="text-sm text-gray-400 mt-1">High energy metal for intense tactical combinations.</p>\
                                    </div>\
                                    <div class="flex items-center gap-6 mt-2">\
                                        <button id="btn-music-prev" class="w-12 h-12 flex items-center justify-center rounded-full bg-[#2D3343] hover:bg-[#3E465B] text-white transition-colors">\
                                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>\
                                        </button>\
                                        <button id="btn-music-play" class="w-16 h-16 flex items-center justify-center rounded-full bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 transition-all hover:scale-105">\
                                            <svg id="icon-play" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>\
                                            <svg id="icon-pause" class="hidden" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>\
                                        </button>\
                                        <button id="btn-music-next" class="w-12 h-12 flex items-center justify-center rounded-full bg-[#2D3343] hover:bg-[#3E465B] text-white transition-colors">\
                                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>\
                                        </button>\
                                    </div>\
                                    <div id="yt-player" class="hidden"></div>\
                                </div>\
                            </div>\
                        </div>' index.html
