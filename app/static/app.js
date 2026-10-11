(function () {
  "use strict";

  function $(id) { return document.getElementById(id); }

  // Keep the chosen files in one list so each picture can be removed.
  var input = $("images");
  var drop = $("drop");
  var thumbs = $("thumbs");
  var picked = $("picked");
  var chosen = [];

  function sync() {
    if (!input) { return; }
    var dt = new DataTransfer();
    chosen.forEach(function (f) { dt.items.add(f); });
    input.files = dt.files;
    if (picked) {
      picked.textContent = chosen.length ? chosen.length + " file" + (chosen.length === 1 ? "" : "s") + " chosen." : "";
    }
    if (!thumbs) { return; }
    thumbs.textContent = "";
    chosen.forEach(function (f, i) {
      var li = document.createElement("li");
      var img = document.createElement("img");
      img.alt = "";
      img.src = URL.createObjectURL(f);
      var name = document.createElement("span");
      name.textContent = f.name;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Remove";
      btn.addEventListener("click", function () { chosen.splice(i, 1); sync(); });
      li.appendChild(img); li.appendChild(name); li.appendChild(btn);
      thumbs.appendChild(li);
    });
  }

  function add(files) {
    Array.prototype.forEach.call(files, function (f) { chosen.push(f); });
    sync();
  }

  if (input) {
    input.addEventListener("change", function () {
      // The browser replaced the list with the new pick; take it as the added files.
      var fresh = Array.prototype.slice.call(input.files);
      var known = chosen.slice();
      chosen = known.concat(fresh.filter(function (f) {
        return !known.some(function (k) { return k.name === f.name && k.size === f.size; });
      }));
      sync();
    });
  }
  if (drop) {
    ["dragenter", "dragover"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("over"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      drop.addEventListener(ev, function () { drop.classList.remove("over"); });
    });
    drop.addEventListener("drop", function (e) {
      e.preventDefault();
      if (e.dataTransfer && e.dataTransfer.files.length) { add(e.dataTransfer.files); }
    });
  }

  // Busy button.
  ["check-form", "batch-form"].forEach(function (id) {
    var form = $(id);
    if (!form) { return; }
    form.addEventListener("submit", function (e) {
      if (id === "check-form") {
        var brand = $("brand_name");
        if (brand && !brand.value.trim()) {
          e.preventDefault();
          var msg = document.getElementById("brand-error");
          if (!msg) {
            msg = document.createElement("p");
            msg.id = "brand-error"; msg.className = "error"; msg.setAttribute("role", "alert");
            brand.insertAdjacentElement("afterend", msg);
          }
          msg.textContent = "Type the brand name from the application.";
          brand.setAttribute("aria-invalid", "true");
          brand.focus();
          return;
        }
      }
      var go = $("go");
      if (go) { go.textContent = go.getAttribute("data-busy"); go.disabled = true; }
    });
  });

  // Fill in the Old Tom example.
  var fill = $("fill-example");
  if (fill) {
    fill.addEventListener("click", function (e) {
      e.preventDefault();
      var v = JSON.parse(fill.getAttribute("data-example"));
      Object.keys(v).forEach(function (k) {
        var radios = document.querySelectorAll('input[type=radio][name="' + k + '"]');
        if (radios.length) {
          radios.forEach(function (r) { r.checked = r.value === v[k]; });
        } else if ($(k)) {
          $(k).value = v[k];
        }
      });
    });
  }

  // Print button opens every row first.
  function openAll() { document.querySelectorAll("details").forEach(function (d) { d.open = true; }); }
  window.addEventListener("beforeprint", openAll);
  var pr = $("print");
  if (pr) {
    pr.addEventListener("click", function () { window.print(); });
    var at = $("printed-at");
    if (at) { at.textContent = "Checked " + new Date().toLocaleString() + "."; }
  }

  // Batch status polling.
  var queue = $("queue");
  if (queue) {
    var job = queue.getAttribute("data-job");
    var only = $("only-look");
    var last = null;

    function render(d) {
      last = d;
      $("summary").textContent = d.done + " of " + d.total + " done. " + d.to_look + " to look at.";
      var tb = queue.querySelector("tbody");
      tb.textContent = "";
      d.items.forEach(function (it) {
        if (only.checked && !it.looks && !it.error) { return; }
        var tr = document.createElement("tr");
        [it.id, it.files, it.summary].forEach(function (t) {
          var td = document.createElement("td"); td.textContent = t; tr.appendChild(td);
        });
        var td = document.createElement("td");
        if (it.state === "done") {
          var a = document.createElement("a");
          a.href = "/batch/" + job + "/item/" + it.n;
          a.textContent = "Open";
          td.appendChild(a);
        }
        tr.appendChild(td);
        tb.appendChild(tr);
      });
    }

    function poll() {
      fetch("/batch/" + job + ".json").then(function (r) {
        if (r.status === 404) { window.location.reload(); return null; }
        return r.json();
      }).then(function (d) {
        if (!d) { return; }
        render(d);
        if (!d.finished) { setTimeout(poll, 2000); }
      }).catch(function () { setTimeout(poll, 4000); });
    }
    only.addEventListener("change", function () { if (last) { render(last); } });
    poll();
  }
})();
