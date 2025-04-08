async function loadGame() {
    document.getElementById("spinner").classList.remove("hidden");
    const res = await fetch("/start");
    const data = await res.json();
    document.getElementById("spinner").classList.add("hidden");
    document.getElementById("title").textContent = data.title;
    document.getElementById("summary").textContent = data.summary;
    document.getElementById("score").textContent = data.score;
    const linkDiv = document.getElementById("links");
    linkDiv.innerHTML = "";
    
    data.links.forEach(link => {
      const a = document.createElement("a");
      a.href = "#";
      a.textContent = link.split("/wiki/")[1].replace(/_/g, " ");
      a.classList.add("text-blue-400", "hover:text-blue-600", "transition-colors", "duration-300");
      a.onclick = () => {
        fetch(`/start?url=${encodeURIComponent(link)}`).then(res => res.json()).then(updateUI);
      };
      linkDiv.appendChild(a);
    });
  }

  function updateUI(data) {
    document.getElementById("title").textContent = data.title;
    document.getElementById("summary").textContent = data.summary;
    document.getElementById("score").textContent = data.score;
    const linkDiv = document.getElementById("links");
    linkDiv.innerHTML = "";
    data.links.forEach(link => {
      const a = document.createElement("a");
      a.href = "#";
      a.textContent = link.split("/wiki/")[1].replace(/_/g, " ");
      a.classList.add("text-blue-400", "hover:text-blue-600", "transition-colors", "duration-300");
      a.onclick = () => {
        fetch(`/start?url=${encodeURIComponent(link)}`).then(res => res.json()).then(updateUI);
      };
      linkDiv.appendChild(a);
    });
  }
  
  loadGame();
  