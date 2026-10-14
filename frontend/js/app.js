const $ = (id) => document.getElementById(id);
const setText = (id, value) => {
  const el = $(id);
  if (el) el.textContent = value;
};
const setClass = (id, value) => {
  const el = $(id);
  if (el) el.className = value;
};


document.querySelectorAll(".nav-item").forEach((a) => {
  a.addEventListener("click", (e) => {
    e.preventDefault();

    const pageId = a.dataset.page;
    const target = document.getElementById(pageId);

    if (!target) {
      console.warn(`Page not found: ${pageId}`);
      return;
    }

    document.querySelectorAll(".page").forEach((page) => {
      page.classList.toggle("active", page.id === pageId);
    });

    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item === a);
    });

    if (pageId === "inventory") loadInventory();
    if (pageId === "history") loadHistory();
    if (pageId === "analytics") loadAnalytics();
    if (pageId === "prediction-vs-actual") loadPredictionVsActual();
    if (pageId === "dashboard") loadDashboard();
    if (pageId === "menu") loadMenuIntelligence();
    if (pageId === "prep") loadPreparationPlans();
    if (pageId === "monitor") loadMonitoring();
  });
});

document.querySelectorAll(".action-card button[data-page]").forEach((button) => {
  button.addEventListener("click", () => {
    const pageId = button.dataset.page;
    const target = document.getElementById(pageId);

    if (!target) {
      console.warn(`Page not found: ${pageId}`);
      return;
    }

    document.querySelectorAll(".page").forEach((page) => {
      page.classList.toggle("active", page.id === pageId);
    });

    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.page === pageId);
    });

    if (pageId === "inventory") loadInventory();
    if (pageId === "prep") loadPreparationPlans();
  });
});

async function loadMenuIntelligence() {
  const catalog = $("menuCatalog");
  const recipesEl = $("recipeIntelligence");

  if (!catalog || !recipesEl) return;

  catalog.innerHTML = `<div class="muted">Loading menu items...</div>`;
  recipesEl.innerHTML = `<div class="muted">Loading recipe intelligence...</div>`;

  try {
    const [menus, recipes] = await Promise.all([
      api("/operations/menus"),
      api("/operations/recipes"),
    ]);

    if (!Array.isArray(menus)) {
      throw new Error("Menu data is not a list.");
    }

    if (!Array.isArray(recipes)) {
      throw new Error("Recipe data is not a list.");
    }

    const ingredientIds = new Set(
      recipes.map((recipe) => recipe.ingredient_id)
    );

    setText("menuCount", menus.length);
    setText("recipeCount", recipes.length);
    setText("ingredientCount", ingredientIds.size);

    catalog.innerHTML = "";

        menus.forEach((menu) => {
      const item = document.createElement("div");
      item.className = "action-item";

      const menuRecipes = recipes.filter(
        (recipe) =>
          String(recipe.menu_item).trim().toLowerCase() ===
          String(menu.menu_name).trim().toLowerCase()
      );

      const portionSize = menuRecipes.reduce(
        (total, recipe) =>
          total + Number(recipe.quantity_per_portion || 0),
        0
      );

      item.innerHTML = `
        <strong>${menu.menu_name}</strong>
        <span class="muted">
          Recipe quantity: ${portionSize.toFixed(3)} kg / portion
        </span>
      `;

      catalog.appendChild(item);
    });

    recipesEl.innerHTML = "";

    const table = document.createElement("table");
    table.className = "data-table compact-table";

    table.innerHTML = `
      <thead>
        <tr>
          <th>Menu Item</th>
          <th>Ingredient</th>
          <th>Quantity / Portion</th>
          <th>Unit</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;

    const body = table.querySelector("tbody");

    recipes.forEach((recipe) => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${recipe.menu_item}</td>
        <td>${recipe.ingredient_id}</td>
        <td>${recipe.quantity_per_portion}</td>
        <td>${recipe.unit}</td>
      `;

      body.appendChild(row);
    });

    recipesEl.appendChild(table);

  } catch (error) {
    catalog.innerHTML = `
      <div class="muted">
        Unable to load menu intelligence: ${error.message || "Backend unavailable."}
      </div>
    `;

    recipesEl.innerHTML = `
      <div class="muted">
        Recipe data could not be loaded.
      </div>
    `;

    setText("menuCount", "—");
    setText("recipeCount", "—");
    setText("ingredientCount", "—");
  }
}

async function loadPredictionVsActual() {
  try {
    const results = await Promise.all([
      api("/predictions"),
      api("/consumption")
    ]);

    const predictions = results[0];
    const consumption = results[1];

    if (!Array.isArray(predictions) ||
        !Array.isArray(consumption)) {
      throw new Error("Invalid API data");
    }

    // Group actual consumption by date and food item.
    const actualMap = new Map();

    consumption.forEach(function (record) {
      const date = String(record.date || "").trim();
      const food = String(record.food_item || "")
        .trim().toLowerCase();
      const actual = Number(record.consumed);

      if (
        !date ||
        !food ||
        date === "string" ||
        food === "string" ||
        !Number.isFinite(actual)
      ) {
        return;
      }

      const key = date + "|" + food;

      if (!actualMap.has(key)) {
        actualMap.set(key, {
          total: 0,
          count: 0
        });
      }

      const entry = actualMap.get(key);
      entry.total += actual;
      entry.count += 1;
    });

    // Keep only the latest prediction per date and food.
    const predictionMap = new Map();

    predictions.forEach(function (record) {
      const date = String(record.date || "").trim();
      const food = String(record.food_item || "")
        .trim().toLowerCase();
      const predicted = Number(record.predicted_demand);

      if (
        !date ||
        !food ||
        !Number.isFinite(predicted)
      ) {
        return;
      }

      const key = date + "|" + food;
      const previous = predictionMap.get(key);

      if (
        !previous ||
        String(record.created_at || "") >
          String(previous.created_at || "")
      ) {
        predictionMap.set(key, {
          date: date,
          food: food,
          food_item: record.food_item,
          predicted: predicted,
          created_at: record.created_at || ""
        });
      }
    });

    // Match predictions with actual consumption.
    const matched = [];

    predictionMap.forEach(function (prediction, key) {
      const actualRecord = actualMap.get(key);

      if (!actualRecord) {
        return;
      }

      matched.push({
        date: prediction.date,
        food_item: prediction.food_item,
        predicted: prediction.predicted,
        actual: actualRecord.total
      });
    });

    matched.sort(function (a, b) {
      return a.date.localeCompare(b.date);
    });

    setText("pvaRecords", matched.length);

    if (matched.length === 0) {
      setText("pvaPredicted", "—");
      setText("pvaActual", "—");
      setText("pvaDifference", "—");
      setText("pvaMae", "—");
      setText("pvaRmse", "—");
      setText("pvaMape", "N/A");

      if (window.__foodwisePredictionActualChart) {
        window.__foodwisePredictionActualChart.destroy();
        window.__foodwisePredictionActualChart = null;
      }

      console.log(
        "No matching date and food-item records found."
      );
      return;
    }

    // Display the most recent matched date.
    const latest = matched[matched.length - 1];

    setText("pvaPredicted", latest.predicted.toFixed(2));
    setText("pvaActual", latest.actual.toFixed(2));
    setText(
      "pvaDifference",
      Math.abs(latest.predicted - latest.actual).toFixed(2)
    );

    // Calculate performance metrics.
    const errors = matched.map(function (item) {
      return item.predicted - item.actual;
    });

    const mae = errors.reduce(function (sum, error) {
      return sum + Math.abs(error);
    }, 0) / errors.length;

    const rmse = Math.sqrt(
      errors.reduce(function (sum, error) {
        return sum + error * error;
      }, 0) / errors.length
    );

    const validRecords = matched.filter(function (item) {
      return item.actual !== 0;
    });

    let mape = null;

    if (validRecords.length > 0) {
      mape = validRecords.reduce(function (sum, item) {
        return sum +
          Math.abs(
            (item.predicted - item.actual) / item.actual
          ) * 100;
      }, 0) / validRecords.length;
    }

    setText("pvaMae", mae.toFixed(2));
    setText("pvaRmse", rmse.toFixed(2));
    setText(
      "pvaMape",
      mape === null ? "N/A" : mape.toFixed(2) + "%"
    );

    // Draw the chart.
    const canvas = $("predictionActualChart");

    console.log("Canvas found:", canvas);
    console.log("Chart.js loaded:", typeof Chart !== "undefined");
    console.log("Matched records:", matched.length);

    if (canvas && typeof Chart !== "undefined") {
      if (window.__foodwisePredictionActualChart) {
        window.__foodwisePredictionActualChart.destroy();
      }

      const chartRecords = matched.slice(-10);

      window.__foodwisePredictionActualChart = new Chart(
        canvas,
        {
          type: "line",
          data: {
            labels: chartRecords.map(function (item) {
              return item.date + " - " + item.food_item;
            }),
           datasets: [
  {
    label: "Predicted Demand",
    data: chartRecords.map(function (item) {
      return Number(item.predicted);
    }),
    borderColor: "#3b82f6",
    backgroundColor: "#3b82f6",
    pointBackgroundColor: "#3b82f6",
    pointRadius: 5,
    pointHoverRadius: 7,
    borderWidth: 3,
    tension: 0.3,
    fill: false,
    spanGaps: true
  },
  {
    label: "Actual Consumption",
    data: chartRecords.map(function (item) {
      return Number(item.actual);
    }),
    borderColor: "#22c55e",
    backgroundColor: "#22c55e",
    pointBackgroundColor: "#22c55e",
    pointRadius: 5,
    pointHoverRadius: 7,
    borderWidth: 3,
    tension: 0.3,
    fill: false,
    spanGaps: true
  }
]
          },
          options: {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    legend: {
      display: true,
      labels: {
        color: "#94a3b8"
      }
    }
  },
  scales: {
    x: {
      ticks: { color: "#94a3b8" },
      grid: {
        color: "rgba(148,163,184,0.12)"
      }
    },
    y: {
      beginAtZero: true,
      ticks: { color: "#94a3b8" },
      grid: {
        color: "rgba(148,163,184,0.12)"
      }
    }
  }
}
        }
      );
    }

    console.log(
      "Prediction vs Actual:",
      matched.length,
      "matched records",
      latest
    );

  } catch (error) {
    console.error("Prediction vs Actual failed:", error);
    setText("pvaRecords", "Error");
  }
}

const searchForm = $("searchForm");
const searchInput = $("searchInput");
const searchStatus = $("searchStatus");

function applySearch(value) {
  const query = String(value || "").trim().toLowerCase();
  const page = document.querySelector(".page.active");
  if (!page) return;

  const rows = [...page.querySelectorAll("tbody tr")];
  const blocks = [...page.querySelectorAll(".card, .kpi-card, .hero-block, .action-item")];
  let matches = 0;

  rows.forEach((row) => {
    const match = !query || row.textContent.toLowerCase().includes(query);
    row.style.display = match ? "" : "none";
    if (match) matches += 1;
  });

  blocks.forEach((block) => {
    if (block.closest("tbody")) return;
    const match = !query || block.textContent.toLowerCase().includes(query);
    block.style.display = match ? "" : "none";
    if (match) matches += 1;
  });

  if (searchStatus) {
    searchStatus.textContent = query && !matches ? "No matching results." : query ? `${matches} matching items` : "";
  }
}

if (searchForm && searchInput) {
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    applySearch(searchInput.value);
  });
  searchInput.addEventListener("search", () => applySearch(searchInput.value));
}

const today = new Date().toISOString().slice(0, 10);
["pDate", "cDate", "wDate"].forEach((x) => {
  const el = $(x);
  if (el) el.value = today;
});

const historyColumns = [
  "date", "day", "expected_attendance", "food_item", "food_prepared",
  "food_consumed", "food_wasted", "holiday", "event", "exam",
  "temperature", "rain_probability",
];

function displayHistoryValue(record, column) {
  const value = record && record[column];
  return value === null || value === undefined || value === "" ? "—" : String(value);
}

async function loadHistory() {
  const status = $("historyStatus");
  const table = $("historyTable");
  const body = $("historyTableBody");
  if (!status || !table || !body) return;

  status.textContent = "Loading historical data...";
  table.hidden = true;
  body.replaceChildren();

  try {
    const records = await api("/history");
    if (!Array.isArray(records)) throw new Error("Historical data response was not a list.");
    if (!records.length) {
      status.textContent = "No historical records are available.";
      return;
    }

    records.forEach((record) => {
      const row = document.createElement("tr");
      historyColumns.forEach((column) => {
        const cell = document.createElement("td");
        cell.textContent = displayHistoryValue(record, column);
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
    status.textContent = `${records.length} historical records loaded.`;
    table.hidden = false;
    applySearch(searchInput ? searchInput.value : "");
  } catch (error) {
    status.textContent = `Unable to load historical data: ${error.message || "Backend unavailable."}`;
  }
}

async function runPrediction() {

  const payload = {
    date: $("pDate").value,
    expected_attendance: +$("pAttend").value,
    food_item: $("pFood").value,
    temperature: +$("pTemp").value,
    rain_probability: +$("pRain").value,
    previous_consumption: +$("pPrev").value,
    holiday: +$("pHoliday").value,
    event: +$("pEvent").value,
    exam: +$("pExam").value,
  };
    // Update Explainable AI immediately from the prediction inputs
    // Update Explainable AI using the prediction form inputs
  const explanationValues = {
    predictionExplainAttendance: `${payload.expected_attendance} people`,
    predictionExplainConsumption: `${payload.previous_consumption} kg`,
    predictionExplainDay: payload.date
      ? new Date(`${payload.date}T00:00:00`).toLocaleDateString(
          "en-IN",
          { weekday: "long" }
        )
      : "Not selected",
    predictionExplainHoliday: payload.holiday ? "Yes" : "No",
    predictionExplainEvent: payload.event ? "Yes" : "No",
    predictionExplainExam: payload.exam ? "Yes" : "No",
    predictionExplainTemperature: `${payload.temperature} °C`,
    predictionExplainRain: `${payload.rain_probability} mm`,
  };

  Object.entries(explanationValues).forEach(([id, value]) => {
    setText(id, value);
  });

  try {
    const d = await api("/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const w = await api("/waste-risk", {
      method: "POST",
      body: JSON.stringify({
        ...payload,
        food_prepared: d.recommended_preparation,
      }),
    });

    const resultEl = $("predictionResult");

    if (resultEl) {
      resultEl.innerHTML = `
        <div class="card">
          <div class="muted">Predicted Demand</div>
          <div class="metric">${d.predicted_demand}</div>
          <div class="muted">kg expected consumption</div>
        </div>

        <div class="card">
          <div class="muted">Prediction Range</div>
          <div class="metric">${d.range_low}–${d.range_high}</div>
          <div class="muted">estimated demand interval</div>
        </div>

        <div class="card">
          <div class="muted">Recommended Preparation</div>
          <div class="metric">${d.recommended_preparation}</div>
          <div class="muted">
            Safety margin: ${d.margin} kg
          </div>
        </div>

        <div class="card">
          <div class="muted">Waste Risk</div>
          <div class="metric ${w.risk}">${w.risk}</div>
        </div>
      `;
    }

    setText("mDemand", d.predicted_demand);
setText("mPrep", d.recommended_preparation);
setText("mRisk", w.risk);
setClass("mRisk", `metric ${w.risk}`);



loadInventory();
  } catch (e) {
    alert(e.message);
  }
}



async function loadInventory() {
  try {
    const data = await api("/inventory");

    const dashboardTable = $("invTable");
    const inventoryTable = $("invTableInventory");

    if (!Array.isArray(data)) {
      throw new Error("Invalid inventory data received");
    }

    // Inventory table on the main dashboard
    const dashboardRows = data.map((item) => {
      const ingredient = item.ingredient || "Unknown";
      const required = Number(item.required) || 0;
      const available = Number(item.available) || 0;
      const unit = item.unit || "kg";

      const shortage = required > available;
      const status = shortage ? "SHORTAGE" : "AVAILABLE";
      const statusClass = shortage ? "red" : "green";

      return `
        <tr>
          <td>${ingredient}</td>
          <td>${required} ${unit}</td>
          <td>${available} ${unit}</td>
          <td>
            <span class="status-badge ${statusClass}">
              ${status}
            </span>
          </td>
        </tr>
      `;
    }).join("");

    // Full inventory table on the Inventory page
    const inventoryRows = data.map((item) => {
      const ingredient = item.ingredient || "Unknown";
      const required = Number(item.required) || 0;
      const available = Number(item.available) || 0;
      const unit = item.unit || "kg";

const shortage = required - available;
const purchase = shortage > 0 ? shortage : 0;

      return `
        <tr>
          <td>${ingredient}</td>
          <td>${available} ${unit}</td>
          <td>${required} ${unit}</td>
          <td>${purchase.toFixed(2)} ${unit}</td>
        </tr>
      `;
    }).join("");

    if (dashboardTable) {
      dashboardTable.innerHTML = dashboardRows;
    }

    if (inventoryTable) {
      inventoryTable.innerHTML = inventoryRows;
    }

  } catch (error) {
    console.error("Inventory load failed:", error);

    const dashboardTable = $("invTable");
    const inventoryTable = $("invTableInventory");

    if (dashboardTable) {
      dashboardTable.innerHTML =
        "<tr><td colspan='4'>Unable to load inventory</td></tr>";
    }

    if (inventoryTable) {
      inventoryTable.innerHTML =
        "<tr><td colspan='4'>Unable to load inventory</td></tr>";
    }
  }
}


async function saveInventory() {
  const ingredient = document.getElementById("invIngredient");
  const available = document.getElementById("invAvailable");
  const required = document.getElementById("invRequired");
  const unit = document.getElementById("invUnit");

  if (!ingredient || !available || !required || !unit) {
    alert("Error: Inventory form fields were not found.");
    return;
  }

  const name = ingredient.value.trim();

  if (!name) {
    alert("Please enter an ingredient name.");
    ingredient.focus();
    return;
  }

  const button = document.querySelector(
    'button[onclick="saveInventory()"]'
  );

  try {
    if (button) {
      button.disabled = true;
      button.textContent = "Saving...";
    }

    const result = await api("/inventory/update", {
      method: "POST",
      body: JSON.stringify({
        ingredient: name,
        available: Number(available.value || 0),
        required: Number(required.value || 0),
        unit: unit.value,
      }),
    });

    console.log("Inventory API response:", result);

    await loadInventory();

    alert("Inventory saved successfully!");
  } catch (error) {
    console.error("Inventory save error:", error);
    alert("Could not save inventory: " + error.message);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Save Inventory";
    }
  }
}


async function saveConsumption() {
  const d = {
    date: $("cDate").value,
    food_item: $("cFood").value,
    prepared: +$("cPrepared").value,
    consumed: +$("cConsumed").value,
    remaining: +$("cRemaining").value,
    wasted: +$("cWasted").value,
  };
  await api("/consumption", { method: "POST", body: JSON.stringify(d) });
  alert("Consumption saved");
  loadAnalytics();
}

/* =====================================
   FOODWISE AI - REAL-TIME MONITORING
===================================== */


async function saveMonitoringRecord() {
    const status = document.getElementById("monitorFormStatus");

    const date = document.getElementById("monitorDate")?.value;
    const meal = document.getElementById("monitorMeal")?.value || "Lunch";
    const food = document.getElementById("monitorFood")?.value.trim();

    const preparedText =
        document.getElementById("monitorInputPrepared")?.value;
    const consumedText =
        document.getElementById("monitorInputConsumed")?.value;
    const remainingText =
        document.getElementById("monitorInputRemaining")?.value;
    const wastedText =
        document.getElementById("monitorInputWasted")?.value;

    const prepared = Number(preparedText);
    const consumed = Number(consumedText);
    const remaining = Number(remainingText);
    const wasted = Number(wastedText);

    const showStatus = message => {
        if (status) status.textContent = message;
    };

    if (
        !date ||
        !food ||
        preparedText == null || preparedText.trim() === "" ||
        consumedText == null || consumedText.trim() === "" ||
        remainingText == null || remainingText.trim() === "" ||
        wastedText == null || wastedText.trim() === ""
    ) {
        showStatus("Please complete all fields.");
        return;
    }

    if (
        ![prepared, consumed, remaining, wasted].every(Number.isFinite) ||
        [prepared, consumed, remaining, wasted].some(n => n < 0)
    ) {
        showStatus("Enter valid, non-negative quantities.");
        return;
    }

    if (consumed + remaining !== prepared) {
        showStatus(
            "Consumed portions + kitchen leftovers must equal prepared portions."
        );
        return;
    }

    try {
        showStatus("Saving record...");

        const result = await api("/consumption", {
            method: "POST",
            body: JSON.stringify({
                date,
                meal,
                food_item: food,
                prepared,
                consumed,
                remaining,
                wasted
            })
        });

        console.log("Monitoring record saved:", result);

        showStatus("Record saved successfully.");

        await loadMonitoring();

        if (typeof loadAnalytics === "function") {
            await loadAnalytics();
        }
    } catch (error) {
        console.error("Save Record failed:", error);
        showStatus("Unable to save: " + error.message);
    }
}



async function loadMonitoring() {
  const body = $("monitorTable");
  if (!body) return;

  try {
    const records = await api("/consumption");

    if (!Array.isArray(records)) {
      throw new Error("Invalid consumption data.");
    }

    // Remove invalid placeholder records without deleting database data.
    const validRecords = records.filter(record =>
      record &&
      record.date &&
      record.date !== "string" &&
      record.food_item &&
      record.food_item !== "string" &&
      [record.prepared, record.consumed, record.remaining, record.wasted]
        .every(value =>
          value !== null &&
          value !== "" &&
          Number.isFinite(Number(value)) &&
          Number(value) >= 0
        )
    );

    // Calculate summary values for the selected date and meal.
    const selectedDate = $("monitorDate")?.value || "";
    const selectedMeal = $("monitorMeal")?.value || "";

    const filtered = validRecords.filter(record =>
      (!selectedDate || record.date === selectedDate) &&
      (!selectedMeal || (record.meal || "Lunch") === selectedMeal)
    );

    const totals = filtered.reduce((sum, record) => {
      sum.prepared += Number(record.prepared);
      sum.consumed += Number(record.consumed);
      sum.remaining += Number(record.remaining);
      sum.wasted += Number(record.wasted);
      return sum;
    }, {
      prepared: 0,
      consumed: 0,
      remaining: 0,
      wasted: 0
    });

    setText("monitorPrepared", totals.prepared);
    setText("monitorConsumed", totals.consumed);
    setText("monitorRemaining", totals.remaining);
    setText("monitorWasted", totals.wasted);

    const progress = totals.prepared > 0
      ? Math.min(100, totals.consumed / totals.prepared * 100)
      : 0;

    const progressBar = $("monitorProgress");
    if (progressBar) {
      progressBar.style.width = `${progress}%`;
    }

    setText(
      "monitorProgressText",
      `${progress.toFixed(1)}% of prepared portions consumed`
    );

    const alertEl = $("monitorAlert");

    if (alertEl) {
      if (filtered.length === 0) {
        alertEl.textContent =
          "No records found for the selected date and meal.";
      } else {
        alertEl.textContent =
          `Records: ${filtered.length} | ` +
          `Plate waste: ${totals.wasted} portions | ` +
          `Kitchen leftovers: ${totals.remaining} portions.`;
      }
    }

    setText(
      "monitorUpdated",
      `Last refreshed: ${new Date().toLocaleTimeString()}`
    );

    // Show ALL valid records in Meal History, not just the selected date.
    const history = [...validRecords].sort((a, b) => {
      const timeA = new Date(a.created_at || a.date).getTime() || 0;
      const timeB = new Date(b.created_at || b.date).getTime() || 0;
      return timeB - timeA;
    });

    body.replaceChildren();

    if (history.length === 0) {
      body.innerHTML =
        '<tr><td colspan="7">No valid meal records available.</td></tr>';
      return;
    }

    history.forEach(record => {
      const row = document.createElement("tr");

      [
        record.date,
        record.meal || "—",
        record.food_item,
        Number(record.prepared),
        Number(record.consumed),
        Number(record.remaining),
        Number(record.wasted)
      ].forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = String(value);
        row.appendChild(cell);
      });

      body.appendChild(row);
    });

  } catch (error) {
    console.error("Monitoring load failed:", error);

    body.innerHTML =
      '<tr><td colspan="7">Unable to load records. Check the backend connection.</td></tr>';

    const status = $("monitorFormStatus");
    if (status) {
      status.textContent =
        "Could not load monitoring data: " + error.message;
    }
  }
}

window.saveMonitoringRecord = saveMonitoringRecord;
window.loadMonitoring = loadMonitoring;


async function saveWaste() {
  const d = {
    date: $("wDate").value,
    food_item: $("wFood").value,
    quantity: +$("wQty").value,
    cost_per_unit: +$("wCost").value,
    reason: $("wReason").value,
  };
  await api("/waste", { method: "POST", body: JSON.stringify(d) });
  alert("Waste record saved");
  loadAnalytics();
}


async function loadAnalytics() {
  const consumedEl = document.getElementById("aConsumedMetric");
  const wastedEl = document.getElementById("aWasted");
  const costEl = document.getElementById("aCost");
  const recordsEl = document.getElementById("aRecords");
  const chartCanvas = document.getElementById("wasteChart");

  if (
    !consumedEl ||
    !wastedEl ||
    !costEl ||
    !recordsEl ||
    !chartCanvas
  ) {
    console.error("Analytics HTML elements are missing.");
    return;
  }

  consumedEl.textContent = "Loading...";
  wastedEl.textContent = "Loading...";
  costEl.textContent = "Loading...";
  recordsEl.textContent = "Loading...";

  try {
    const [consumptionResult, wasteResult, historyResult] =
      await Promise.allSettled([
        api("/consumption"),
        api("/waste"),
        api("/history")
      ]);

    function getArray(result, name) {
      if (result.status !== "fulfilled") {
        console.error(`${name} API failed:`, result.reason);
        return [];
      }

      const data = result.value;

      if (Array.isArray(data)) return data;

      if (data && Array.isArray(data.records)) return data.records;
      if (data && Array.isArray(data.items)) return data.items;
      if (data && Array.isArray(data.data)) return data.data;

      console.warn(`${name} API did not return a record array.`, data);
      return [];
    }

    function validNumber(value) {
      return value !== null &&
        value !== undefined &&
        value !== "" &&
        Number.isFinite(Number(value));
    }

    function validConsumption(record) {
      return record &&
        typeof record === "object" &&
        record.date !== "string" &&
        record.food_item !== "string" &&
        validNumber(record.consumed) &&
        Number(record.consumed) >= 0;
    }

    function validWaste(record) {
      return record &&
        typeof record === "object" &&
        record.date !== "string" &&
        record.food_item !== "string" &&
        validNumber(record.quantity) &&
        Number(record.quantity) >= 0;
    }

    function validHistory(record) {
      return record &&
        typeof record === "object" &&
        record.date !== "string" &&
        record.food_item !== "string";
    }

    const consumption = getArray(
      consumptionResult,
      "Consumption"
    ).filter(validConsumption);

    const waste = getArray(
      wasteResult,
      "Waste"
    ).filter(validWaste);

    const history = getArray(
      historyResult,
      "Historical data"
    ).filter(validHistory);

    // Total food actually eaten, from consumption records.
    const totalConsumed = consumption.reduce(
      (sum, record) => sum + Number(record.consumed),
      0
    );

    // Total recorded waste, from the dedicated waste records.
    const totalWasted = waste.reduce(
      (sum, record) => sum + Number(record.quantity),
      0
    );

    // Use the saved total cost when available; otherwise calculate it.
    const totalWasteCost = waste.reduce((sum, record) => {
      if (validNumber(record.cost)) {
        return sum + Number(record.cost);
      }

      if (validNumber(record.cost_per_unit)) {
        return sum +
          Number(record.quantity) * Number(record.cost_per_unit);
      }

      return sum;
    }, 0);

    consumedEl.textContent =
      Math.round(totalConsumed).toLocaleString("en-IN");

    wastedEl.textContent =
      Math.round(totalWasted).toLocaleString("en-IN");

    costEl.textContent =
      "₹" + totalWasteCost.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });

    recordsEl.textContent =
      history.length.toLocaleString("en-IN");

    // Build the chart from real waste records, grouped by date.
    const wasteByDate = {};

    waste.forEach(record => {
      const date = record.date || "Unknown date";
      wasteByDate[date] =
        (wasteByDate[date] || 0) + Number(record.quantity);
    });

    const sortedDates = Object.keys(wasteByDate).sort();

    if (window.wasteChartInstance) {
      window.wasteChartInstance.destroy();
    }

    const context = chartCanvas.getContext("2d");

    window.wasteChartInstance = new Chart(context, {
      type: "bar",
      data: {
        labels: sortedDates,
        datasets: [{
          label: "Recorded Food Waste",
          data: sortedDates.map(date => wasteByDate[date]),
          backgroundColor: "rgba(239, 100, 100, 0.75)",
          borderColor: "rgb(220, 70, 70)",
          borderWidth: 1,
          borderRadius: 5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true
          },
          tooltip: {
            callbacks: {
              label: context =>
                `${context.dataset.label}: ${context.parsed.y}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Waste Quantity"
            }
          },
          x: {
            title: {
              display: true,
              text: "Date"
            }
          }
        }
      }
    });

    if (
      consumptionResult.status === "rejected" ||
      wasteResult.status === "rejected" ||
      historyResult.status === "rejected"
    ) {
      console.warn(
        "Some Analytics data could not be loaded. Check the failed API requests."
      );
    }

    console.log("Analytics loaded:", {
      consumptionRecords: consumption.length,
      wasteRecords: waste.length,
      historicalRecords: history.length,
      totalConsumed,
      totalWasted,
      totalWasteCost
    });

  } catch (error) {
    console.error("Analytics loading error:", error);

    consumedEl.textContent = "Error";
    wastedEl.textContent = "Error";
    costEl.textContent = "Error";
    recordsEl.textContent = "Error";
  }
}


async function loadDashboard() {
  try {
    const [recommendations, predictions, consumption] = await Promise.all([
      api("/recommendations"),
      api("/predictions"),
      api("/consumption"),
    ]);

    const recEl = $("recs");
    if (recEl) {
      recEl.innerHTML = recommendations.recommendations.map((x) => `<div class="recommend">${x}</div>`).join("");
    }

    const latestPrediction = predictions[predictions.length - 1];
    const latestConsumption = consumption[consumption.length - 1];
    if (latestPrediction) {
      setText("mDemand", latestPrediction.predicted_demand);
      setText("mPrep", latestPrediction.recommended_preparation);
      setText("forecastDemand", latestPrediction.predicted_demand);
      setText("forecastPrep", latestPrediction.recommended_preparation);
    }

    if (latestConsumption) {
      setText("mRisk", "Recorded");
      setClass("mRisk", "metric LOW");
    }

    const predCanvas = $("predChart");
    if (predCanvas) {
      if (window.__foodwisePredChart) window.__foodwisePredChart.destroy();
      window.__foodwisePredChart = new Chart(predCanvas, {
        type: "line",
        data: {
          labels: predictions.slice(-8).map((x) => x.date),
          datasets: [
            { label: "Predicted", data: predictions.slice(-8).map((x) => x.predicted_demand), borderColor: "#2563eb", tension: 0.3 },
            {
              label: "Consumed",
              data: predictions.slice(-8).map((x) => {
                const match = consumption.find((c) => c.date === x.date && c.food_item === x.food_item);
                return match ? match.consumed : null;
              }),
              borderColor: "#16a34a",
              tension: 0.3,
              spanGaps: true,
            },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }

    await loadAnalytics();
  } catch (e) {
    const recEl = $("recs");
    if (recEl) recEl.innerHTML = `<div class="recommend">Backend connection unavailable.</div>`;
    console.warn("Dashboard load failed:", e);
  }
}

async function simulate() {
  const d = await api("/simulate", {
    method: "POST",
    body: JSON.stringify({
      expected_attendance: +$("sAttend").value,
      temperature: +$("sTemp").value,
      rain_probability: +$("sRain").value,
      previous_consumption: +$("sPrev").value,
      holiday: +$("sHoliday").value,
      event: +$("sEvent").value,
    }),
  });
  const result = $("simResult");
  if (result) {
    result.innerHTML = `<div class="card"><div class="muted">Predicted Demand</div><div class="metric">${d.demand.predicted_demand}</div></div><div class="card"><div class="muted">Recommended Preparation</div><div class="metric">${d.demand.recommended_preparation}</div></div><div class="card"><div class="muted">Waste Risk</div><div class="metric ${d.waste.risk}">${d.waste.risk}</div></div>`;
  }
}

loadDashboard();

/* Make functions accessible to HTML onclick handlers */
window.saveInventory = saveInventory;
window.loadInventory = loadInventory;
window.runPrediction = runPrediction;
window.saveConsumption = saveConsumption;
window.saveWaste = saveWaste;
window.simulate = simulate;
window.loadDashboard = loadDashboard;
window.loadAnalytics = loadAnalytics;
window.loadHistory = loadHistory;
window.loadMenuIntelligence = loadMenuIntelligence;
window.loadPredictionVsActual = loadPredictionVsActual;

/* =====================================
   FOODWISE AI - PREPARATION PLANNING
===================================== */

function loadPreparationPlans() {
  const table = document.getElementById("prepTable");
  if (!table) return;

  const plans = JSON.parse(
    localStorage.getItem("foodwisePreparationPlans") || "[]"
  );

  if (plans.length === 0) {
    table.innerHTML = `
      <tr>
        <td colspan="7">No preparation plans saved yet.</td>
      </tr>
    `;
    return;
  }

  table.innerHTML = plans.map(plan => `
    <tr>
      <td>${plan.date}</td>
      <td>${plan.meal}</td>
      <td>${plan.food}</td>
      <td>${plan.attendance}</td>
      <td>${plan.predicted}</td>
      <td>${plan.recommended}</td>
      <td>${plan.actual === "" ? "Pending" : plan.actual}</td>
    </tr>
  `).join("");
}

function savePreparationPlan() {
  const date = document.getElementById("prepDate").value;
  const meal = document.getElementById("prepMeal").value;
  const food = document.getElementById("prepFood").value;
  const attendance = document.getElementById("prepAttendance").value;
  const predicted = document.getElementById("prepPredicted").value;
  const recommended = document.getElementById("prepRecommended").value;
  const actual = document.getElementById("prepActual").value;
  const status = document.getElementById("prepStatus");

  if (!date || !attendance || !predicted || !recommended) {
    status.textContent = "Please complete all required fields.";
    return;
  }

  if (
    Number(attendance) < 1 ||
    Number(predicted) < 0 ||
    Number(recommended) < 0 ||
    (actual !== "" && Number(actual) < 0)
  ) {
    status.textContent = "Please enter valid, non-negative quantities.";
    return;
  }

  const plans = JSON.parse(
    localStorage.getItem("foodwisePreparationPlans") || "[]"
  );

  const plan = {
    id: Date.now(),
    date,
    meal,
    food,
    attendance: Number(attendance),
    predicted: Number(predicted),
    recommended: Number(recommended),
    actual
  };

  plans.push(plan);

  try {
    localStorage.setItem(
      "foodwisePreparationPlans",
      JSON.stringify(plans)
    );
  } catch (error) {
    status.textContent = "Could not save the plan in this browser.";
    return;
  }

  status.textContent = "Preparation plan saved successfully!";
  loadPreparationPlans();
}
 
document.addEventListener("DOMContentLoaded", loadPreparationPlans);
window.savePreparationPlan = function () {
  const date = document.getElementById("prepDate").value;
  const meal = document.getElementById("prepMeal").value;
  const food = document.getElementById("prepFood").value;
  const attendance = document.getElementById("prepAttendance").value;
  const predicted = document.getElementById("prepPredicted").value;
  const recommended = document.getElementById("prepRecommended").value;
  const actual = document.getElementById("prepActual").value;
  const status = document.getElementById("prepStatus");

  if (!date || !attendance || !predicted || !recommended) {
    status.textContent = "Please fill in all required fields.";
    return;
  }

  const key = "foodwisePreparationPlans";
  let plans = [];

  try {
    plans = JSON.parse(localStorage.getItem(key) || "[]");
  } catch (error) {
    status.textContent = "Could not read saved plans.";
    return;
  }

  plans.push({
    date,
    meal,
    food,
    attendance: Number(attendance),
    predicted: Number(predicted),
    recommended: Number(recommended),
    actual: actual === "" ? "" : Number(actual)
  });

  try {
    localStorage.setItem(key, JSON.stringify(plans));
    status.textContent = "Preparation plan saved successfully!";

    const table = document.getElementById("prepTable");
    table.innerHTML = plans.map(plan => `
      <tr>
        <td>${plan.date}</td>
        <td>${plan.meal}</td>
        <td>${plan.food}</td>
        <td>${plan.attendance}</td>
        <td>${plan.predicted}</td>
        <td>${plan.recommended}</td>
        <td>${plan.actual === "" ? "Pending" : plan.actual}</td>
      </tr>
    `).join("");
  } catch (error) {
    status.textContent = "Could not save the plan in this browser.";
  }
};

async function loadSustainability() {
  const status = $("susStatus");
  const table = $("susWasteTable");

  status.textContent = "Loading sustainability data...";
  table.innerHTML = "";

  try {
    const records = await api("/waste");

    // Ignore invalid or incomplete records.
    const validRecords = (Array.isArray(records) ? records : []).filter(
      (record) =>
        record &&
        typeof record.food_item === "string" &&
        record.food_item.trim() !== "" &&
        Number.isFinite(Number(record.quantity)) &&
        Number(record.quantity) >= 0 &&
        Number.isFinite(Number(record.cost_per_unit)) &&
        Number(record.cost_per_unit) >= 0 &&
        !Number.isNaN(Date.parse(record.date))
    );

    const totalWaste = validRecords.reduce(
      (sum, record) => sum + Number(record.quantity),
      0
    );

    const totalCost = validRecords.reduce(
      (sum, record) =>
        sum + Number(record.quantity) * Number(record.cost_per_unit),
      0
    );

    $("susTotalWaste").textContent =
      totalWaste.toLocaleString("en-IN", {
        maximumFractionDigits: 2
      });

    $("susWasteCost").textContent =
      totalCost.toLocaleString("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
      });

    $("susWasteRecords").textContent =
      validRecords.length.toLocaleString("en-IN");

    // Calculate utilization only from valid consumption records.
    $("susUtilization").textContent = "—";

    try {
      const consumption = await api("/consumption");

      const validConsumption = (
        Array.isArray(consumption) ? consumption : []
      ).filter(
        (record) =>
          record &&
          typeof record.food_item === "string" &&
          record.food_item.trim() !== "" &&
          !Number.isNaN(Date.parse(record.date)) &&
          Number.isFinite(Number(record.prepared)) &&
          Number(record.prepared) > 0 &&
          Number.isFinite(Number(record.consumed)) &&
          Number(record.consumed) >= 0 &&
          Number(record.consumed) <= Number(record.prepared)
      );

      const preparedTotal = validConsumption.reduce(
        (sum, record) => sum + Number(record.prepared),
        0
      );

      const consumedTotal = validConsumption.reduce(
        (sum, record) => sum + Number(record.consumed),
        0
      );

      if (preparedTotal > 0) {
        $("susUtilization").textContent =
          ((consumedTotal / preparedTotal) * 100).toFixed(1) + "%";
      }
    } catch (error) {
      console.warn("Could not load consumption for utilization:", error);
    }

    if (validRecords.length === 0) {
      table.innerHTML = `
        <tr>
          <td colspan="5">No valid waste records are available yet.</td>
        </tr>
      `;

      status.textContent =
        "No valid waste records found. Save a waste record to begin tracking.";
      return;
    }

    table.innerHTML = validRecords
      .slice()
      .sort((a, b) => b.date.localeCompare(a.date))
      .map((record) => {
        const quantity = Number(record.quantity);
        const unitCost = Number(record.cost_per_unit);
        const wasteCost = quantity * unitCost;

        const cell = (value) =>
          String(value ?? "Not recorded").replace(
            /[&<>"']/g,
            (character) =>
              ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
              })[character]
          );

        return `
          <tr>
            <td>${cell(record.food_item)}</td>
            <td>${quantity.toLocaleString("en-IN", {
              maximumFractionDigits: 2
            })}</td>
            <td>${unitCost.toLocaleString("en-IN", {
              style: "currency",
              currency: "INR"
            })}</td>
            <td>${wasteCost.toLocaleString("en-IN", {
              style: "currency",
              currency: "INR"
            })}</td>
            <td>${cell(record.reason)}</td>
          </tr>
        `;
      })
      .join("");

    status.textContent =
      `Showing ${validRecords.length} valid waste records from the backend.`;
  } catch (error) {
    console.error("Sustainability loading failed:", error);

    $("susTotalWaste").textContent = "—";
    $("susWasteCost").textContent = "—";
    $("susWasteRecords").textContent = "—";
    $("susUtilization").textContent = "—";

    table.innerHTML = `
      <tr>
        <td colspan="5">Unable to load waste records. Please try again.</td>
      </tr>
    `;

    status.textContent =
      "Could not connect to the backend. Check that the API server is running.";
  }
}

async function loadRecommendations() {
  const status = document.getElementById("recStatus");
  const actionList = document.getElementById("recActionList");

  const predictionCount = document.getElementById("recPredictionCount");
  const wasteAlerts = document.getElementById("recWasteAlerts");
  const inventoryCount = document.getElementById("recInventoryCount");

  status.textContent = "Loading recommendation data...";
  actionList.innerHTML = "";

  try {
    const [predictions, waste, inventory] = await Promise.all([
      api("/predictions"),
      api("/waste"),
      api("/inventory")
    ]);

    const validPredictions = Array.isArray(predictions)
      ? predictions.filter(p =>
          p &&
          Number.isFinite(Number(p.predicted_demand))
        )
      : [];

    const validWaste = Array.isArray(waste)
      ? waste.filter(w =>
          w &&
          Number.isFinite(Number(w.quantity)) &&
          Number(w.quantity) > 0
        )
      : [];

    const validInventory = Array.isArray(inventory)
      ? inventory.filter(i => i && typeof i === "object")
      : [];

    predictionCount.textContent = validPredictions.length;
    wasteAlerts.textContent = validWaste.length;
    inventoryCount.textContent = validInventory.length;

    const recommendations = [];

    if (validPredictions.length > 0) {
      recommendations.push({
        title: "Review demand predictions",
        message:
          `${validPredictions.length} valid prediction records are available. ` +
          "Compare predicted demand with actual consumption before finalizing preparation."
      });
    } else {
      recommendations.push({
        title: "Record demand predictions",
        message:
          "No valid prediction records were found. Run Demand AI and save prediction results first."
      });
    }

    if (validWaste.length > 0) {
      const totalWaste = validWaste.reduce(
        (sum, item) => sum + Number(item.quantity),
        0
      );

      const reasons = {};

      validWaste.forEach(item => {
        const reason = item.reason || "Unspecified";
        reasons[reason] = (reasons[reason] || 0) + 1;
      });

      const mainReason = Object.entries(reasons)
        .sort((a, b) => b[1] - a[1])[0];

      recommendations.push({
        title: "Review recorded food waste",
        message:
          `${totalWaste} units of waste are recorded across ` +
          `${validWaste.length} entries. ` +
          (mainReason
            ? `The most frequently recorded reason is "${mainReason[0]}". Review these records to identify possible improvements.`
            : "Review the recorded reasons to identify possible improvements.")
      });
    } else {
      recommendations.push({
        title: "Improve waste tracking",
        message:
          "No valid waste records were found. Record waste quantities and reasons to support useful recommendations."
      });
    }

    if (validInventory.length > 0) {
      const shortages = validInventory.filter(item => {
        const available = Number(item.available);
        const required = Number(item.required);

        return (
          Number.isFinite(available) &&
          Number.isFinite(required) &&
          available < required
        );
      });

      recommendations.push({
        title: shortages.length > 0
          ? "Review ingredient shortages"
          : "Verify inventory readiness",
        message: shortages.length > 0
          ? `${shortages.length} inventory items have recorded availability below their requirement. Check stock before preparation.`
          : "Inventory records are available. Verify required quantities and available stock before preparing meals."
      });
    } else {
      recommendations.push({
        title: "Update inventory records",
        message:
          "No inventory records were returned. Add ingredient availability and required quantities to support purchasing decisions."
      });
    }

    recommendations.forEach(item => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.marginTop = "12px";

      const heading = document.createElement("h3");
      heading.textContent = item.title;

      const description = document.createElement("p");
      description.className = "muted";
      description.textContent = item.message;

      card.append(heading, description);
      actionList.appendChild(card);
    });

    status.textContent =
      "Recommendations generated from the backend records returned.";

  } catch (error) {
    console.error("Failed to load AI recommendations:", error);

    status.textContent =
      "Could not load recommendation data. Check the backend and API endpoints.";

    actionList.textContent =
      "Recommendation data could not be loaded. Verify that /api/predictions, /api/waste, and /api/inventory are working.";
  }
}


