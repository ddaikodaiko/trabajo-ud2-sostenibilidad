// Barra: marca el apartado que se está leyendo y lo mantiene visible en el móvil
(function () {
  var enlaces = Array.prototype.slice.call(document.querySelectorAll(".barra__lista a"));
  if (!enlaces.length || !("IntersectionObserver" in window)) return;
  var secciones = enlaces.map(function (a) { return document.querySelector(a.getAttribute("href")); });
  var visibles = {};
  function marcar(i) {
    enlaces.forEach(function (a, j) {
      if (j === i) {
        if (a.getAttribute("aria-current") !== "true") {
          a.setAttribute("aria-current", "true");
          var lista = a.closest(".barra__lista");
          if (lista && lista.scrollWidth > lista.clientWidth) lista.scrollTo({ left: Math.max(a.offsetLeft - 16, 0), behavior: "smooth" });
        }
      } else a.removeAttribute("aria-current");
    });
  }
  var obs = new IntersectionObserver(function (entradas) {
    entradas.forEach(function (e) { visibles[e.target.id] = e.isIntersecting; });
    for (var i = secciones.length - 1; i >= 0; i--) {
      if (secciones[i] && visibles[secciones[i].id]) { marcar(i); return; }
    }
    marcar(-1);
  }, { rootMargin: "0px 0px -55% 0px" });
  secciones.forEach(function (s) { if (s) obs.observe(s); });
})();

// Gráficos: al pasar el ratón o el dedo, globo con el año y el valor más cercanos
(function () {
  var globo = document.querySelector(".globo");
  if (!globo) return;
  function formato(v, u, signo) {
    var s = Math.abs(v).toFixed(1).replace(".", ",");
    if (v < 0) s = "−" + s; else if (signo && v > 0) s = "+" + s;
    return s + " " + (u === "m" ? "m de agua eq." : u);
  }
  document.querySelectorAll(".grafico[data-grafico]").forEach(function (fig) {
    var d = JSON.parse(fig.getAttribute("data-grafico"));
    var svg = fig.querySelector("svg");
    var guia = svg.querySelector(".g__guia");
    var n = d.x.length;
    function mover(cx, cy) {
      var r = svg.getBoundingClientRect();
      var px = (cx - r.left) / r.width * d.an;
      var izq = d.i, der = d.an - d.d;
      var t = (px - izq) / (der - izq);
      if (t < -0.03 || t > 1.03) { ocultar(); return; }
      var i = Math.max(0, Math.min(n - 1, Math.round(t * (n - 1))));
      if (d.tipo === "barras") i = Math.max(0, Math.min(n - 1, Math.floor(t * n)));
      var xv = d.tipo === "barras" ? izq + (i + 0.5) * (der - izq) / n : izq + i / (n - 1) * (der - izq);
      guia.setAttribute("x1", xv); guia.setAttribute("x2", xv); guia.removeAttribute("hidden");
      globo.innerHTML = "<b>" + d.x[i] + "</b>: " + formato(d.y[i], d.u, d.s);
      globo.hidden = false;
      globo.style.left = (r.left + xv / d.an * r.width) + "px";
      globo.style.top = (r.top + 8) + "px";
    }
    function ocultar() { globo.hidden = true; guia.setAttribute("hidden", ""); }
    svg.addEventListener("pointermove", function (e) { mover(e.clientX, e.clientY); });
    svg.addEventListener("pointerdown", function (e) { mover(e.clientX, e.clientY); });
    svg.addEventListener("pointerleave", ocultar);
    window.addEventListener("scroll", ocultar, { passive: true });
  });
})();

// Fotos: si alguna no llega a cargar, se retira sin descolocar la página
(function () {
  document.querySelectorAll("img[data-foto]").forEach(function (img) {
    function retirar() { var f = img.closest(".foto"); if (f) f.hidden = true; }
    img.addEventListener("error", retirar);
    if (img.complete && img.currentSrc && img.naturalWidth === 0) retirar();
  });
})();
