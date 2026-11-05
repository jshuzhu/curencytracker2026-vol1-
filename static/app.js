/* ==========================================================
   CurrencyBot – app.js
   Clean, accessible logic for dropdown-based converter
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const amountInput    = document.getElementById("amountInput");
  const fromSelect     = document.getElementById("fromCurrency");
  const toSelect       = document.getElementById("toCurrency");
  const swapBtn        = document.getElementById("swapBtn");
  const convertBtn     = document.getElementById("convertBtn");
  const resultBox      = document.getElementById("resultBox");
  const resultMain     = document.getElementById("resultMain");
  const resultDetails  = document.getElementById("resultDetails");
  const statusBadge    = document.getElementById("statusBadge");
  const ratesBody      = document.getElementById("ratesBody");
  const ratesLastUpdated = document.getElementById("ratesLastUpdated");
  const quickButtons   = document.querySelectorAll(".quick-btn");
  const nlForm         = document.getElementById("nlForm");
  const nlInput        = document.getElementById("nlInput");
  const nlOutput       = document.getElementById("nlOutput");

  // Currency display names
  const currencyNames = {
    USD: "US Dollar",      EUR: "Euro",            GBP: "British Pound",
    MYR: "Ringgit",        SGD: "Singapore Dollar", JPY: "Japanese Yen",
    AUD: "Australian Dollar", CAD: "Canadian Dollar", CHF: "Swiss Franc",
    CNY: "Chinese Yuan",   HKD: "Hong Kong Dollar", INR: "Indian Rupee",
    IDR: "Indonesian Rupiah", KRW: "South Korean Won", NZD: "NZ Dollar",
    PHP: "Philippine Peso", THB: "Thai Baht",       TWD: "Taiwan Dollar",
    VND: "Vietnamese Dong", AED: "UAE Dirham",      SAR: "Saudi Riyal",
    BRL: "Brazilian Real",  MXN: "Mexican Peso",    ZAR: "SA Rand",
    TRY: "Turkish Lira",    SEK: "Swedish Krona",   NOK: "Norwegian Krone",
    DKK: "Danish Krone",    PLN: "Polish Zloty"
  };

  const currencyFlags = {
    USD: "\u{1F1FA}\u{1F1F8}", EUR: "\u{1F1EA}\u{1F1FA}", GBP: "\u{1F1EC}\u{1F1E7}",
    MYR: "\u{1F1F2}\u{1F1FE}", SGD: "\u{1F1F8}\u{1F1EC}", JPY: "\u{1F1EF}\u{1F1F5}",
    AUD: "\u{1F1E6}\u{1F1FA}", CAD: "\u{1F1E8}\u{1F1E6}", CHF: "\u{1F1E8}\u{1F1ED}",
    CNY: "\u{1F1E8}\u{1F1F3}", HKD: "\u{1F1ED}\u{1F1F0}", INR: "\u{1F1EE}\u{1F1F3}",
    IDR: "\u{1F1EE}\u{1F1E9}", KRW: "\u{1F1F0}\u{1F1F7}", NZD: "\u{1F1F3}\u{1F1FF}",
    PHP: "\u{1F1F5}\u{1F1ED}", THB: "\u{1F1F9}\u{1F1ED}", TWD: "\u{1F1F9}\u{1F1FC}",
    VND: "\u{1F1FB}\u{1F1F3}", AED: "\u{1F1E6}\u{1F1EA}", SAR: "\u{1F1F8}\u{1F1E6}",
    BRL: "\u{1F1E7}\u{1F1F7}", MXN: "\u{1F1F2}\u{1F1FD}", ZAR: "\u{1F1FF}\u{1F1E6}",
    TRY: "\u{1F1F9}\u{1F1F7}", SEK: "\u{1F1F8}\u{1F1EA}", NOK: "\u{1F1F3}\u{1F1F4}",
    DKK: "\u{1F1E9}\u{1F1F0}", PLN: "\u{1F1F5}\u{1F1F1}"
  };

  // Zero-decimal currencies
  const zeroDecimal = new Set(["JPY","KRW","VND","IDR"]);

  function formatAmount(val, code) {
    if (zeroDecimal.has(code)) {
      return Number(val).toLocaleString("en-US", { maximumFractionDigits: 0 });
    }
    return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatRate(val) {
    if (val >= 100)  return val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (val >= 0.01) return val.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
    return val.toLocaleString("en-US", { minimumFractionDigits: 6, maximumFractionDigits: 6 });
  }

  // ---- Convert button ----
  convertBtn.addEventListener("click", () => {
    const amount = parseFloat(amountInput.value);
    if (!amount || amount <= 0) {
      resultMain.textContent = "Please enter a valid amount.";
      resultDetails.textContent = "";
      resultBox.style.display = "block";
      return;
    }
    const from = fromSelect.value;
    const to   = toSelect.value;
    runDropdownConversion(amount, from, to);
  });

  // Also convert on Enter inside the amount field
  amountInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); convertBtn.click(); }
  });

  // ---- Swap button ----
  swapBtn.addEventListener("click", () => {
    const tmp = fromSelect.value;
    fromSelect.value = toSelect.value;
    toSelect.value = tmp;
    // Re-run conversion if a result is already showing
    if (resultBox.style.display !== "none") {
      convertBtn.click();
    }
  });

  // ---- Quick convert buttons ----
  quickButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetCode = btn.getAttribute("data-to");
      const amount = parseFloat(amountInput.value) || 100;
      fromSelect.value = "USD";
      toSelect.value = targetCode;
      amountInput.value = amount;
      runDropdownConversion(amount, "USD", targetCode);
    });
  });

  // ---- Core dropdown conversion ----
  async function runDropdownConversion(amount, from, to) {
    resultMain.textContent = "Calculating...";
    resultDetails.textContent = "";
    resultBox.style.display = "block";

    const query = `${amount} ${from} to ${to}`;
    try {
      const resp = await fetch(`/api/convert?q=${encodeURIComponent(query)}`);
      const data = await resp.json();

      if (!data.success) {
        resultMain.textContent = data.formatted_output;
        resultDetails.textContent = "";
        return;
      }

      // Parse amounts from the formatted output
      const lines = data.formatted_output.split("\n");

      // Find the result line (e.g. "100.00 USD = 406.47 MYR")
      const resultLine = lines.find(l => l.includes("=") && l.includes(from) && l.includes(to));
      if (resultLine) {
        resultMain.textContent = resultLine.trim();
      } else {
        resultMain.textContent = lines[1] || "Conversion complete";
      }

      // Build details
      const rateLine = lines.find(l => l.startsWith("\u2022 Rate:") || l.startsWith("* Rate:") || (l.includes("Rate:") && l.includes("1 ")));
      const updatedLine = lines.find(l => l.includes("Last Updated:"));
      const inverseLine = lines.find(l => l.includes("Inverse:"));

      let details = [];
      if (rateLine) details.push(rateLine.replace(/^[\u2022*]\s*/, "").trim());
      if (inverseLine) details.push(inverseLine.replace(/^[\u2022*]\s*/, "").trim());
      if (updatedLine) details.push(updatedLine.replace(/^[\u2022*]\s*/, "").trim());
      resultDetails.innerHTML = details.join("<br>");

    } catch (err) {
      resultMain.textContent = "Could not connect to server.";
      resultDetails.textContent = "Please check your connection and try again.";
    }
  }

  // ---- Load rates table ----
  async function loadRates() {
    try {
      const resp = await fetch("/api/rates");
      const data = await resp.json();

      if (data.is_cached) {
        statusBadge.textContent = "Offline / Cached";
        statusBadge.classList.add("offline");
      } else {
        statusBadge.textContent = "Live Rates";
        statusBadge.classList.remove("offline");
      }

      ratesLastUpdated.textContent = "Last updated: " + data.last_updated;

      ratesBody.innerHTML = "";
      const order = ["EUR","GBP","MYR","SGD","JPY","AUD","CAD","CHF","CNY","INR","KRW","THB","IDR","PHP","HKD","TWD","VND","NZD","AED","SAR","BRL","MXN","ZAR","TRY","SEK","NOK","DKK","PLN"];

      for (const code of order) {
        const rate = data.rates[code];
        if (rate === undefined) continue;
        const tr = document.createElement("tr");
        const flag = currencyFlags[code] || "";
        const name = currencyNames[code] || code;
        tr.innerHTML = `
          <td>${flag} <strong>${code}</strong> - ${name}</td>
          <td>${formatRate(rate)}</td>
        `;
        // Click row to convert
        tr.style.cursor = "pointer";
        tr.addEventListener("click", () => {
          fromSelect.value = "USD";
          toSelect.value = code;
          convertBtn.click();
          window.scrollTo({ top: 0, behavior: "smooth" });
        });
        ratesBody.appendChild(tr);
      }
    } catch {
      statusBadge.textContent = "Offline";
      statusBadge.classList.add("offline");
      ratesLastUpdated.textContent = "Could not load rates.";
    }
  }

  // ---- Natural language form (advanced) ----
  if (nlForm) {
    nlForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const q = nlInput.value.trim();
      if (!q) return;
      nlOutput.style.display = "block";
      nlOutput.textContent = "Calculating...";
      try {
        const resp = await fetch(`/api/convert?q=${encodeURIComponent(q)}`);
        const data = await resp.json();
        nlOutput.textContent = data.formatted_output;
      } catch (err) {
        nlOutput.textContent = "Error: " + err.message;
      }
    });
  }

  // ---- Init ----
  loadRates();
});
