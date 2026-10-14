/* IAS-Viewer-Server dashboard.
   Query params: ?monitor=mon1  (pick a monitor profile)
*/
(async function () {
  const qs = new URLSearchParams(location.search);
  const grid = document.getElementById("grid");
  const sel = document.getElementById("monitorSel");

  const res = await fetch("/api/cameras");
  const data = await res.json();
  // If the configured HLS host is localhost, use the page's own host instead,
  // so monitors opening the dashboard via the server's LAN IP just work.
  let hlsBase = (data.hls_base || "http://localhost:8888").replace(/\/$/, "");
  try {
    const u = new URL(hlsBase);
    if (u.hostname === "localhost" || u.hostname === "127.0.0.1") {
      u.hostname = location.hostname;
      hlsBase = u.toString().replace(/\/$/, "");
    }
  } catch (e) { /* keep hlsBase as-is */ }

  Object.entries(data.monitors || {}).forEach(([id, name]) => {
    const o = document.createElement("option");
    o.value = id; o.textContent = name; sel.appendChild(o);
  });
  const mon = qs.get("monitor") || Object.keys(data.monitors || {})[0] || "mon1";
  sel.value = mon;
  sel.onchange = () => {
    qs.set("monitor", sel.value);
    location.search = qs.toString();
  };

  document.getElementById("fsAll").onclick = () => {
    document.documentElement.requestFullscreen?.();
  };

  const cams = (data.cameras || []).filter(c => (c.monitor || "mon1") === mon);
  if (!cams.length) {
    grid.innerHTML = '<p style="color:#8b93a7">دوربینی برای این مانیتور تعریف نشده است.</p>';
    return;
  }

  cams.forEach(cam => {
    const tile = document.createElement("div");
    tile.className = "tile";
    tile.innerHTML = `<video muted playsinline></video>
      <div class="label"><span></span><button>⛶</button></div>`;
    tile.querySelector("span").textContent = cam.name || cam.id;
    tile.querySelector("button").onclick = () => tile.requestFullscreen?.();
    grid.appendChild(tile);

    const video = tile.querySelector("video");
    const src = `${hlsBase}/${encodeURIComponent(cam.id)}/index.m3u8`;
    if (window.Hls && Hls.isSupported()) {
      const hls = new Hls({ maxBufferLength: 10 });
      hls.loadSource(src);
      hls.attachMedia(video);
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src; // Safari native HLS
    }
    video.play().catch(() => {});
  });
})();
