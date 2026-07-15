sed -i '/<button id="btn-music-prev"/,/<\/button>/c\
                                        <button id="btn-music-prev-song" class="w-10 h-10 flex items-center justify-center rounded-full bg-[#2D3343] hover:bg-[#3E465B] text-white transition-colors" title="Previous Song">\
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>\
                                        </button>\
                                        <button id="btn-music-rewind" class="w-12 h-12 flex items-center justify-center rounded-full bg-[#2D3343] hover:bg-[#3E465B] text-white transition-colors" title="Rewind 15s">\
                                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>\
                                            <span class="absolute text-[9px] font-bold mt-1 ml-0.5">15</span>\
                                        </button>' index.html
sed -i '/<button id="btn-music-next"/,/<\/button>/c\
                                        <button id="btn-music-forward" class="w-12 h-12 flex items-center justify-center rounded-full bg-[#2D3343] hover:bg-[#3E465B] text-white transition-colors" title="Forward 15s">\
                                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11V9a4 4 0 0 0-4-4H3"></path><polyline points="17 23 21 19 17 15"></polyline><path d="M3 13v2a4 4 0 0 0 4 4h14"></path></svg>\
                                            <span class="absolute text-[9px] font-bold mt-1 mr-0.5">15</span>\
                                        </button>\
                                        <button id="btn-music-next-song" class="w-10 h-10 flex items-center justify-center rounded-full bg-[#2D3343] hover:bg-[#3E465B] text-white transition-colors" title="Next Song">\
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>\
                                        </button>' index.html
