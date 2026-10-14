
(function () {
  const STORAGE_KEY = "foodwisePreparationPlans";

  function getPlans() {
    try {
      const plans = JSON.parse(
        localStorage.getItem(STORAGE_KEY) || "[]"
      );
      return Array.isArray(plans) ? plans : [];
    } catch (error) {
      console.error("Error reading preparation plans:", error);
      return [];
    }
  }

  function renderPlans() {
    const table = document.getElementById("prepTable");
    if (!table) return;

    const plans = getPlans();
    table.replaceChildren();

    if (plans.length === 0) {
      const row = table.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 7;
      cell.textContent = "No preparation plans saved yet.";
      return;
    }

    plans.slice().reverse().forEach(function (plan) {
      const row = table.insertRow();

      [
        plan.date,
        plan.meal,
        plan.food,
        plan.attendance,
        plan.predicted,
        plan.recommended,
        plan.actual === "" ? "Pending" : plan.actual
      ].forEach(function (value) {
        row.insertCell().textContent = String(value ?? "");
      });
    });
  }

  window.savePreparationPlan = function () {
    const status = document.getElementById("prepStatus");

    try {
      const date = document.getElementById("prepDate").value;
      const meal = document.getElementById("prepMeal").value;
      const food = document.getElementById("prepFood").value;
      const attendance =
        document.getElementById("prepAttendance").value;
      const predicted =
        document.getElementById("prepPredicted").value;
      const recommended =
        document.getElementById("prepRecommended").value;
      const actual =
        document.getElementById("prepActual").value;

      if (!date) {
        status.textContent = "Please select a preparation date.";
        return;
      }

      if (attendance.trim() === "") {
        status.textContent = "Please enter expected attendance.";
        return;
      }

      if (predicted.trim() === "") {
        status.textContent = "Please enter predicted demand.";
        return;
      }

      if (recommended.trim() === "") {
        status.textContent = "Please enter recommended preparation.";
        return;
      }

      if (
        Number(attendance) < 1 ||
        Number(predicted) < 0 ||
        Number(recommended) < 0 ||
        (actual !== "" && Number(actual) < 0) ||
        !Number.isFinite(Number(attendance)) ||
        !Number.isFinite(Number(predicted)) ||
        !Number.isFinite(Number(recommended)) ||
        (actual !== "" && !Number.isFinite(Number(actual)))
      ) {
        status.textContent = "Please enter valid quantities.";
        return;
      }

      const plans = getPlans();

      plans.push({
        date: date,
        meal: meal,
        food: food,
        attendance: Number(attendance),
        predicted: Number(predicted),
        recommended: Number(recommended),
        actual: actual === "" ? "" : Number(actual)
      });

      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(plans)
      );

      renderPlans();
      status.textContent = "Preparation plan saved successfully!";
    } catch (error) {
      console.error("Preparation save error:", error);
      status.textContent = "Save failed. Check the browser console.";
    }
  };

  renderPlans();
})();
