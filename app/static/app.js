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
    var old = document.getElementById("size-error");
    if (old) { old.remove(); }
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

  // Phone photos can be 5 MB or more, and the host refuses one upload over about 32 MB.
  // Big pictures are shrunk here to 2000 pixels on the long side, which is still more
  // than the reader uses (1600). The file name is kept so spreadsheet rows still match.
  var MAX_SIDE = 2000;
  var UPLOAD_LIMIT = 30 * 1024 * 1024;
  var preparing = 0;

  function shrink(f) {
    if (!/^image\/(jpeg|png|webp)$/.test(f.type) || f.size < 1500000 || !window.createImageBitmap) {
      return Promise.resolve(f);
    }
    return createImageBitmap(f, { imageOrientation: "from-image" }).then(function (bmp) {
      var scale = Math.min(1, MAX_SIDE / Math.max(bmp.width, bmp.height));
      var c = document.createElement("canvas");
      c.width = Math.round(bmp.width * scale);
      c.height = Math.round(bmp.height * scale);
      c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
      return new Promise(function (resolve) {
        c.toBlob(function (b) {
          resolve(b && b.size < f.size ? new File([b], f.name, { type: "image/jpeg", lastModified: f.lastModified }) : f);
        }, "image/jpeg", 0.9);
      });
    }).catch(function () { return f; });
  }

  function busy(on) {
    var go = $("go");
    if (!go) { return; }
    if (!go.getAttribute("data-idle")) { go.setAttribute("data-idle", go.textContent); }
    go.disabled = on;
    go.textContent = on ? "Preparing pictures..." : go.getAttribute("data-idle");
  }

  function same(a, b) { return a.name === b.name && a.lastModified === b.lastModified; }

  function add(files) {
    var fresh = Array.prototype.slice.call(files).filter(function (f) {
      return !chosen.some(function (k) { return same(k, f); });
    });
    if (!fresh.length) { sync(); return; }
    preparing += 1; busy(true);
    Promise.all(fresh.map(shrink)).then(function (small) {
      chosen = chosen.concat(small);
      sync();
      warmBatch();
    }).finally(function () {
      preparing -= 1;
      if (!preparing) { busy(false); }
    });
  }

  if (input) {
    input.addEventListener("change", function () {
      // The browser replaced the list with the new pick; take it as the added files.
      if (input.files.length) { add(input.files); }
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

  // Once files are picked on the batch page (see add), wake whatever does the batch work,
  // at most once a minute. Never on page load, so just looking at the page costs nothing.
  var warmedAt = 0;
  function warmBatch() {
    if (!$("batch-form") || !chosen.length || Date.now() - warmedAt < 60000) { return; }
    warmedAt = Date.now();
    fetch("/batch/warm").catch(function () {});
  }

  // Busy button.
  ["check-form", "batch-form"].forEach(function (id) {
    var form = $(id);
    if (!form) { return; }
    form.addEventListener("submit", function (e) {
      if (preparing) { e.preventDefault(); return; }
      var total = chosen.reduce(function (s, f) { return s + f.size; }, 0);
      var sheet = $("spreadsheet");
      if (sheet && sheet.files.length) { total += sheet.files[0].size; }
      if (total > UPLOAD_LIMIT) {
        e.preventDefault();
        var big = document.getElementById("size-error");
        if (!big) {
          big = document.createElement("p");
          big.id = "size-error"; big.className = "error"; big.setAttribute("role", "alert");
          ($("drop") || form).insertAdjacentElement("afterend", big);
        }
        big.textContent = "These files add up to " + Math.round(total / 1048576) + " MB. One upload can take up to " +
          "30 MB (about 60 phone photos, or a few hundred label image files). Split them into smaller batches.";
        return;
      }
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
