"use strict";

const form = document.querySelector("#filters");

if (form) {
  const query = document.querySelector("#query");
  const task = document.querySelector("#task");
  const material = document.querySelector("#material");
  const sale = document.querySelector("#sale");
  const count = document.querySelector("#count");
  const empty = document.querySelector("#empty");
  const more = document.querySelector("#more");
  const filterGroups = [...form.querySelectorAll("[data-filter-group]")];
  const pageSize = 18;
  const materials = {
    metal: ["cut", "bend", "metal", "finish"],
    wood: ["wood"],
    stone: ["stone"],
    forms: ["stone"],
  };
  const normalize = (text) => text.toLocaleLowerCase("ru").replaceAll("ё", "е").trim();
  const products = [...document.querySelectorAll(".product")].map((card) => ({
    card,
    task: card.dataset.task,
    types: JSON.parse(card.dataset.types),
    search: normalize(card.querySelector("h2").textContent + " " + card.dataset.types + " " + card.querySelector(".product-note").textContent),
    sale: card.dataset.sale === "true",
  }));
  let limit = pageSize;

  function updateGroups() {
    for (const group of filterGroups) {
      group.hidden = Boolean(task.value && group.dataset.filterGroup !== task.value);
      if (group.hidden) {
        for (const input of group.querySelectorAll("input")) input.checked = false;
      }
    }
  }

  function render() {
    const words = normalize(query.value).split(/\s+/).filter(Boolean);
    const types = new Set([...form.querySelectorAll("details input:checked")].map((input) => input.value));
    let matches = 0;
    for (const product of products) {
      const matchesMaterial = !material.value || (
        materials[material.value].includes(product.task) &&
        (material.value !== "stone" || product.types.some((type) => type.includes("по камню"))) &&
        (material.value !== "forms" || product.types.some((type) => type.includes("оснастки")))
      );
      const match = (!task.value || product.task === task.value) &&
        matchesMaterial && (!sale.checked || product.sale) &&
        (!types.size || product.types.some((type) => types.has(type))) &&
        words.every((word) => product.search.includes(word));
      if (match) matches += 1;
      product.card.hidden = !match || matches > limit;
    }
    count.textContent = `Найдено: ${matches} · показано: ${Math.min(limit, matches)}`;
    empty.hidden = matches > 0;
    more.hidden = matches <= limit;
  }

  const initialTask = new URLSearchParams(location.search).get("task");
  if ([...task.options].some((option) => option.value === initialTask)) {
    task.value = initialTask;
  }
  updateGroups();
  render();
  form.hidden = false;

  form.addEventListener("submit", (event) => event.preventDefault());
  form.addEventListener("input", (event) => {
    limit = pageSize;
    if (event.target === task) updateGroups();
    render();
  });
  form.addEventListener("reset", () => {
    requestAnimationFrame(() => {
      limit = pageSize;
      updateGroups();
      render();
    });
  });
  more.addEventListener("click", () => {
    limit += pageSize;
    const previouslyVisible = new Set(products.filter(({ card }) => !card.hidden));
    render();
    const next = products.find((product) => !previouslyVisible.has(product) && !product.card.hidden);
    next?.card.querySelector("a").focus({ preventScroll: true });
    next?.card.scrollIntoView({ block: "nearest" });
  });
}
