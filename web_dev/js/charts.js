/* charts.js – Chart.js wrapper */

const _charts = {};

function destroyChart(id) {
  if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
}

function _baseOpts(extra = {}) {
  const base = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { labels: { color: '#8892a4', font: { size: 11 } } },
      tooltip: { backgroundColor: '#1a1f2e', borderColor: '#2d3344', borderWidth: 1 },
    },
    scales: {
      x: {
        ticks: { color: '#8892a4', font: { size: 10 } },
        grid:  { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        ticks: {
          color: '#8892a4', font: { size: 10 },
          callback: v => '$' + v.toLocaleString('en-US', { maximumFractionDigits: 0 }),
        },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
    },
  };

  /* Deep-merge plugins and scales so base dark-theme styling is preserved */
  if (extra.plugins) {
    base.plugins = { ...base.plugins };
    for (const [k, v] of Object.entries(extra.plugins)) {
      base.plugins[k] = typeof v === 'object' && !Array.isArray(v)
        ? { ...(base.plugins[k] || {}), ...v }
        : v;
    }
  }
  if (extra.scales) {
    for (const axis of ['x', 'y']) {
      if (extra.scales[axis]) {
        const { ticks: exTicks, grid: exGrid, ...exRest } = extra.scales[axis];
        base.scales[axis] = { ...base.scales[axis], ...exRest };
        if (exTicks) base.scales[axis].ticks = { ...base.scales[axis].ticks, ...exTicks };
        if (exGrid)  base.scales[axis].grid  = { ...base.scales[axis].grid,  ...exGrid };
      }
    }
  }

  const { plugins: _p, scales: _s, ...rest } = extra;
  return { ...base, ...rest };
}

function createLineChart(id, datasets, labels, extra = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  _charts[id] = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: _baseOpts(extra),
  });
}

function createBarChart(id, datasets, labels, extra = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  _charts[id] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: _baseOpts(extra),
  });
}

function createPieChart(id, labels, data, colors) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  _charts[id] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderColor: '#1a1f2e', borderWidth: 2 }],
    },
    options: {
      responsive:           true,
      maintainAspectRatio:  false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#8892a4', font: { size: 11 }, padding: 14 },
        },
        tooltip: {
          backgroundColor: '#1a1f2e',
          borderColor:     '#2d3344',
          borderWidth:     1,
          callbacks: {
            label: ctx => ` ${ctx.label}: ${fmt(ctx.raw)}`,
          },
        },
      },
    },
  });
}

function createAreaChart(id, datasets, labels, extra = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  const filled = datasets.map(ds => ({ fill: true, ...ds }));
  _charts[id] = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: filled },
    options: _baseOpts(extra),
  });
}
