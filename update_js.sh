sed -i 's/title: "Metallica Compilation",/title: "Metallica Compilation",\n                artist: "Metallica",/g' index.html
sed -i 's/title: "Lofi Girl Radio",/title: "Lofi Girl Radio",\n                artist: "Lofi Girl",/g' index.html
sed -i 's/title: "World Cup Music",/title: "World Cup Music",\n                artist: "Shakira & Various Artists",/g' index.html

sed -i '/document.getElementById("music-title").innerText = track.title;/a\
            document.getElementById("music-artist").innerText = track.artist;' index.html
