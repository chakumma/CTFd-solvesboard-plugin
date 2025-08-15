const updateIntervalInMillis = 300000;

const update = () => {
  window.location.reload();
};

const getSessionCategory = () => sessionStorage.getItem('category');

const filterByCategory = () => {
  const category = getSessionCategory();
  document.querySelectorAll('[data-category]').forEach((element) => {
    element.style.display = '';
    if (!category || element.dataset.category === category) {
      return;
    }
    element.style.display = 'none';
  });
};

const sortByScore = () => {
  const category = getSessionCategory();
  const activeTab = sessionStorage.getItem('activeTab');
  const parent = activeTab === 'users' ? '#solvesboard-users-pane' : '#solvesboard-teams-pane';
  const tbody = document.querySelector(`${parent} tbody`);
  const rows = Array.from(document.querySelectorAll(`${parent} tbody tr`));

  rows.forEach((row) => {
    let score = 0;
    row
      .querySelectorAll(category ? `[data-category='${category}']` : '[data-category]')
      .forEach((element) => {
        score += parseInt(element.dataset.value);
      });
    row.querySelector('[data-score]').textContent = score.toString();
  });

  rows.sort((a, b) => {
    const scoreA = parseInt(a.querySelector('[data-score]').textContent);
    const scoreB = parseInt(b.querySelector('[data-score]').textContent);
    if (scoreA !== scoreB) {
      return scoreB - scoreA;
    }

    const solverIdA = parseInt(a.dataset.solverId);
    const solverIdB = parseInt(b.dataset.solverId);
    return solverIdA - solverIdB;
  });

  tbody.innerHTML = '';
  rows.forEach((row, index) => {
    row.cells[0].textContent = (index + 1).toString();
    tbody.appendChild(row);
  });
};

const setupCategory = () => {
  const categorySelect = document.getElementById('solvesboard-category-select');
  const category = getSessionCategory();
  if (category) {
    categorySelect.value = category;
    filterByCategory();
    sortByScore();
  }

  categorySelect.addEventListener('change', (event) => {
    const changed = event.target.value;
    sessionStorage.setItem('category', changed);
    filterByCategory();
    sortByScore();
  });
};

const setupTab = () => {
  const teamsTab = document.getElementById('solvesboard-teams-tab');
  const usersTab = document.getElementById('solvesboard-users-tab');
  if (sessionStorage.getItem('activeTab') === 'users') {
    usersTab.click();
  }

  teamsTab.addEventListener('click', () => {
    sessionStorage.setItem('activeTab', 'teams');
    filterByCategory();
    sortByScore();
  });
  usersTab.addEventListener('click', () => {
    sessionStorage.setItem('activeTab', 'users');
    filterByCategory();
    sortByScore();
  });
};

document.addEventListener('DOMContentLoaded', () => {
  setupCategory();
  setupTab();
  setInterval(update, updateIntervalInMillis);
});
