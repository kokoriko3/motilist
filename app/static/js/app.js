const STORAGE_KEY = 'mochilist_v13_data';

const defaultChecklistTemplate = [
  {
    checklist_id: 'c1',
    title: '必需品',
    items: [
      { checklist_item_id: 'c1_i1', item_name: '現金・カード', is_checked: false, quantity: '' },
      { checklist_item_id: 'c1_i2', item_name: '航空券', is_checked: false, quantity: '' }
    ]
  },
  {
    checklist_id: 'c2',
    title: '衣類',
    items: [
      { checklist_item_id: 'c2_i1', item_name: '着替え', is_checked: false, quantity: '' }
    ]
  }
];

const initialData = {
  plans: [
    {
      plan_id: 'p1',
      title: '福岡 2泊3日',
      departure: '現在地',
      destination: '福岡',
      start_date: '2025-01-01',
      days: '3',
      companion_count: 1,
      options: {
        transport: '未設定',
        accommodation: '未設定',
        purpose: ['観光'],
        needs: [],
        visibility: 'private',
        description: '',
        price_range: '-',
        stay_locations: []
      },
      checklist: JSON.parse(JSON.stringify(defaultChecklistTemplate)),
      created_at: '2024/11/15',
      updated_at: '2024/11/15'
    }
  ],
  publicPlans: [
    {
      plan_id: 'pub1',
      title: '京都 古都巡り',
      departure: '東京',
      destination: '京都',
      start_date: '2024-12-10',
      days: '3',
      companion_count: 1,
      options: {
        transport: '新幹線',
        accommodation: 'ゲストハウス',
        purpose: ['観光'],
        needs: [],
        visibility: 'public',
        description: '',
        price_range: '3~4万円',
        stay_locations: ['祇園', '嵐山']
      },
      checklist: JSON.parse(JSON.stringify(defaultChecklistTemplate)),
      created_at: '2024/10/01',
      updated_at: '2024/10/01'
    }
  ]
};

const app = {
  data: null,
  state: { currentPlanId: null, isPublicView: false, tempPurposes: [], deletingPlanId: null },

  init: () => {
    const saved = localStorage.getItem(STORAGE_KEY);
    app.data = saved ? JSON.parse(saved) : JSON.parse(JSON.stringify(initialData));
    if (!app.data.publicPlans) app.data.publicPlans = initialData.publicPlans;
  },
  saveData: () => localStorage.setItem(STORAGE_KEY, JSON.stringify(app.data)),

  login: () => { document.getElementById('profileMenu').hidden = true; app.router.go('list'); },
  register: () => { app.router.go('register-complete'); },
  logout: () => { document.getElementById('profileMenu').hidden = true; app.router.go('login'); },

  router: {
    go: (viewId) => {
      document.querySelectorAll('main > section[id^="view-"]').forEach(el => el.hidden = true);
      const target = document.getElementById('view-' + viewId);
      if (target) target.hidden = false;

      const header = document.getElementById('siteHeader');
      if (['login', 'register', 'register-complete'].includes(viewId)) {
        if (header) header.style.display = 'none';
        document.body.classList.add('auth-mode');
      } else {
        if (header) header.style.display = 'flex';
        document.body.classList.remove('auth-mode');
        document.querySelectorAll('.nav-link').forEach(btn => {
          const targetTab = btn.dataset.target;
          let isActive = false;
      if (targetTab === 'own') {
        if (['list', 'create', 'plan-edit', 'workspace'].includes(viewId)) isActive = true;
        if (viewId === 'detail' && !app.state.isPublicView) isActive = true;
      } else if (targetTab === 'public') {
        if (viewId === 'public-list') isActive = true;
        if (viewId === 'detail' && app.state.isPublicView) isActive = true;
      }
      if (isActive) btn.classList.add('active'); else btn.classList.remove('active');
    });

    if (viewId === 'create') {
      app.state.tempPurposes = [];
      const input = document.getElementById('create-purpose-input');
      if (input) input.value = '';
      app.renderChips('create');
    }

    if (viewId === 'list') app.renderPlanList();
    if (viewId === 'public-list') app.renderPublicPlanList();
  }

      if (!app.state.currentPlanId && app.data.plans.length) {
        app.state.currentPlanId = app.data.plans[0].plan_id;
      }
      if (viewId === 'detail') app.loadPlanDetail(app.state.currentPlanId, app.state.isPublicView);
      if (viewId === 'workspace') app.loadWorkspace();
      if (viewId === 'list') app.bindSearch('plan-search-input', app.renderPlanList);
      if (viewId === 'public-list') app.bindSearch('public-plan-search-input', app.renderPublicPlanList);
    }
  },

  toggleOrigin: (val) => {
    const input = document.getElementById('create-origin-input');
    if (!input) return;
    input.disabled = val !== 'custom';
    if (val === 'custom') input.focus(); else input.value = '';
  },
  bindSearch: (inputId, renderFn) => {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.bound) return;
    input.dataset.bound = '1';
    input.addEventListener('input', renderFn);
  },
  addPurposeChip: (context) => {
    const input = document.getElementById(`${context}-purpose-input`);
    if (!input) return;
    const val = input.value.trim();
    if (val && !app.state.tempPurposes.includes(val)) {
      app.state.tempPurposes.push(val); input.value = ''; app.renderChips(context);
    }
  },
  removePurposeChip: (val, context) => {
    app.state.tempPurposes = app.state.tempPurposes.filter(p => p !== val); app.renderChips(context);
  },
  renderChips: (context) => {
    const container = document.getElementById(`${context}-purpose-list`);
    if (!container) return;
    container.innerHTML = '';
    app.state.tempPurposes.forEach(p => {
      const chip = document.createElement('span'); chip.className = 'chip is-selected';
      chip.innerHTML = `<span class="chip__label">${p}</span><button type="button" class="chip__remove" onclick="app.removePurposeChip('${p}', '${context}')">&times;</button>`;
      container.appendChild(chip);
    });
  },
  createPlan: () => {
    const destInput = document.getElementById('create-destination');
    if (!destInput) return;
    const dest = destInput.value;
    if (!dest) return;
    const needs = Array.from(document.querySelectorAll('input[name="needs"]:checked')).map(cb => cb.value);
    const originRadio = document.querySelector('input[name="origin"]:checked').value;
    const originText = originRadio === 'custom' ? document.getElementById('create-origin-input').value : '現在地';
    const dateVal = document.getElementById('create-date').value;

    const newPlan = {
      plan_id: 'p_' + Date.now(),
      title: dest + '旅行',
      destination: dest,
      departure: originText,
      start_date: dateVal,
      days: document.getElementById('create-days').value,
      companion_count: 1,
      options: {
        needs: needs,
        purpose: [...app.state.tempPurposes],
        transport: '未設定',
        accommodation: '未設定',
        visibility: 'private',
        description: '',
        price_range: '-',
        stay_locations: []
      },
      checklist: JSON.parse(JSON.stringify(defaultChecklistTemplate)),
      created_at: new Date().toLocaleDateString(),
      updated_at: new Date().toLocaleDateString()
    };
    app.data.plans.unshift(newPlan);
    app.saveData();
    app.state.tempPurposes = [];
    app.renderChips('create');
    destInput.value = '';
    document.getElementById('create-days').value = '';
    document.getElementById('create-date').value = '';
    document.querySelectorAll('input[name="needs"]').forEach(cb => cb.checked = false);
    app.state.currentPlanId = newPlan.plan_id;
    app.loadWorkspace();
  },

  renderPlanList: () => {
    const container = document.getElementById('planListContainer');
    if (!container) return;
    container.innerHTML = '';
    const empty = container.parentElement.querySelector('.empty-state');
    if (empty) empty.remove();

    const query = (document.getElementById('plan-search-input')?.value || '').trim().toLowerCase();
    const filtered = app.data.plans.filter(plan => {
      const opts = plan.options || {};
      const haystack = [
        plan.title,
        plan.destination,
        plan.departure,
        opts.transport,
        opts.accommodation,
        opts.description,
        (opts.purpose || []).join(' ')
      ].filter(Boolean).join(' ').toLowerCase();
      return haystack.includes(query);
    });

    if (filtered.length === 0) {
      const emptyNode = document.createElement('div');
      emptyNode.className = 'empty-state';
      emptyNode.textContent = '該当するプランがありません';
      container.parentElement.appendChild(emptyNode);
      return;
    }

    filtered.forEach(plan => {
      const tile = document.createElement('article'); tile.className = 'plan-tile';
      tile.onclick = (e) => {
        if (!e.target.closest('button') && !e.target.closest('.plan-tile__delete')) {
          app.loadPlanDetail(plan.plan_id, false);
          app.router.go('detail');
        }
      };
      tile.innerHTML = `
        <button class="plan-tile__delete" onclick="app.openDeleteModal('${plan.plan_id}'); event.stopPropagation();" title="削除">×</button>
        <div class="plan-tile__header"><p class="plan-tile__title">${plan.title}</p><p class="plan-tile__date">${plan.start_date} ${plan.days}日間</p></div>
        <dl class="plan-tile__list"><div><dt>交通</dt><dd>${(plan.options||{}).transport || ''}</dd></div><div><dt>宿泊</dt><dd>${(plan.options||{}).accommodation || ''}</dd></div></dl>
        <div class="plan-tile__footer">
            <button class="plan-tile__share" onclick="app.openShareModal('${plan.plan_id}'); event.stopPropagation();">共有</button>
            <button class="plan-tile__detail" onclick="app.loadPlanDetail('${plan.plan_id}', false); app.router.go('detail'); event.stopPropagation();">詳細 へ</button>
        </div>
      `;
      container.appendChild(tile);
    });
  },
  renderPublicPlanList: () => {
    const container = document.getElementById('publicPlanListContainer'); if (!container) return;
    container.innerHTML = '';
    const empty = container.parentElement.querySelector('.empty-state');
    if (empty) empty.remove();

    const query = (document.getElementById('public-plan-search-input')?.value || '').trim().toLowerCase();
    const filtered = app.data.publicPlans.filter(plan => {
      const opts = plan.options || {};
      const haystack = [
        plan.title,
        plan.destination,
        opts.transport,
        opts.accommodation,
        opts.description,
        (opts.purpose || []).join(' ')
      ].filter(Boolean).join(' ').toLowerCase();
      return haystack.includes(query);
    });

    if (filtered.length === 0) {
      const emptyNode = document.createElement('div');
      emptyNode.className = 'empty-state';
      emptyNode.textContent = '該当するプランがありません';
      container.parentElement.appendChild(emptyNode);
      return;
    }

    filtered.forEach(plan => {
      const tile = document.createElement('article'); tile.className = 'plan-tile';
      tile.onclick = () => { app.loadPlanDetail(plan.plan_id, true); app.router.go('detail'); };
      tile.innerHTML = `
        <div class="plan-tile__header"><p class="plan-tile__title">${plan.title}</p><p class="plan-tile__date">${plan.start_date} ${plan.days}日間</p></div>
        <dl class="plan-tile__list"><div><dt>交通</dt><dd>${(plan.options||{}).transport || ''}</dd></div><div><dt>宿泊</dt><dd>${(plan.options||{}).accommodation || ''}</dd></div></dl>
        <div class="plan-tile__footer">
          <button class="plan-tile__share" onclick="app.openShareModal('${plan.plan_id}'); event.stopPropagation();">共有</button>
          <button class="plan-tile__detail">詳細を見る</button>
        </div>
      `;
      container.appendChild(tile);
    });
  },

  openShareModal: (planId) => {
    const url = window.location.origin + "/share/" + planId;
    const input = document.getElementById('shareUrl');
    if (input) input.value = url;
    document.getElementById('shareModal').classList.add('is-open');
  },
  closeShareModal: () => {
    document.getElementById('shareModal').classList.remove('is-open');
  },
  copyShareUrl: () => {
    const copyText = document.getElementById("shareUrl");
    if (!copyText) return;
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(copyText.value).then(() => {
      alert("コピーしました: " + copyText.value);
    });
  },
  openDeleteModal: (planId) => {
    app.state.deletingPlanId = planId;
    document.getElementById('deleteModal').classList.add('is-open');
  },
  closeDeleteModal: () => {
    app.state.deletingPlanId = null;
    document.getElementById('deleteModal').classList.remove('is-open');
  },
  deletePlan: () => {
    if (app.state.deletingPlanId) {
      app.data.plans = app.data.plans.filter(p => p.plan_id !== app.state.deletingPlanId);
      app.saveData();
      app.renderPlanList();
      app.closeDeleteModal();
    }
  },

  openFinishModal: () => {
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!plan) return;
    document.getElementById('finish-title').value = plan.title;
    const opts = plan.options || {};
    document.getElementById('finish-desc').value = opts.description || '';
    const vis = opts.visibility || 'private';
    const radio = document.querySelector(`input[name="visibility"][value="${vis}"]`);
    if (radio) radio.checked = true;
    document.getElementById('finishModal').classList.add('is-open');
  },
  closeFinishModal: () => {
    document.getElementById('finishModal').classList.remove('is-open');
  },
  completePlan: () => {
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (plan) {
      plan.title = document.getElementById('finish-title').value;
      if (!plan.options) plan.options = {};
      plan.options.description = document.getElementById('finish-desc').value;
      plan.options.visibility = document.querySelector('input[name="visibility"]:checked').value;
      app.saveData();
      app.closeFinishModal();
      app.loadPlanDetail(plan.plan_id, false);
      app.router.go('detail');
    }
  },

  loadPlanDetail: (planId, isPublic) => {
    app.state.currentPlanId = planId; app.state.isPublicView = isPublic;
    const plan = isPublic ? app.data.publicPlans.find(p => p.plan_id === planId) : app.data.plans.find(p => p.plan_id === planId);
    if (!plan) return;

    document.getElementById('summary-title').textContent = plan.title;
    document.getElementById('summary-date').textContent = `${plan.start_date} (${plan.days}日間)`;
    const opts = plan.options || {};
    document.getElementById('summary-transport').textContent = opts.transport || '未定';
    document.getElementById('summary-stay').textContent = opts.accommodation || '未定';
    document.getElementById('summary-stay-bold').textContent = opts.accommodation || '未定';
    document.getElementById('summary-created').textContent = `作成日: ${plan.created_at || '2024/01/01'}`;
    document.getElementById('summary-price').textContent = `予算目安: ${opts.price_range || '-'}`;
    const desc = (opts.description || '').trim();
    document.getElementById('summary-description').textContent = desc || '説明が未入力です。';

    const locList = document.getElementById('summary-locations');
    const stays = opts.stay_locations || [];
    locList.innerHTML = (stays.length) ? stays.map(l => `<li>${l}</li>`).join('') : '<li>(未設定)</li>';

    let count = 0;
    (plan.checklist || []).forEach(c => count += (c.items || []).length);
    document.getElementById('summary-items-count').textContent = `アイテム総数 ${count}`;

    const packTable = document.getElementById('summary-packing-table');
    packTable.innerHTML = `<thead><tr><th>カテゴリ</th><th>アイテム</th></tr></thead><tbody>
      ${plan.checklist.map(c => {
        const names = (c.items || []).slice(0, 2).map(i => {
          const qty = i.quantity ? ` (${i.quantity})` : '';
          return `${i.item_name}${qty}`;
        }).join(', ');
        return `<tr><td>${c.title}</td><td>${names}</td></tr>`;
      }).join('')}
    </tbody>`;

    const actionsDiv = document.getElementById('summary-actions');
    if (isPublic) {
      actionsDiv.innerHTML = `<button class="save-plan-button" onclick="app.savePublicPlan()">自分のプランとして保存する</button>`;
    } else {
      actionsDiv.innerHTML = `
        <button class="save-plan-button" onclick="app.loadPlanEdit()">プランを編集</button>
        <button class="save-plan-button" style="margin-top:8px; background:#4b5563;" onclick="app.loadWorkspace()">工程を編集（予約・リスト）</button>
      `;
    }
  },

  savePublicPlan: () => {
    const planId = app.state.currentPlanId;
    const publicPlan = app.data.publicPlans.find(p => p.plan_id === planId);
    if (!publicPlan) return;

    const newPlan = JSON.parse(JSON.stringify(publicPlan));
    newPlan.plan_id = 'p_' + Date.now();
    newPlan.title = newPlan.title;
    newPlan.status = '計画中';
    newPlan.created_at = new Date().toLocaleDateString();
    newPlan.updated_at = newPlan.created_at;
    if (!newPlan.options) newPlan.options = {};
    newPlan.options.visibility = 'private';

    app.data.plans.unshift(newPlan);
    app.saveData();
    alert('自分のプランとして保存しました');
    app.loadPlanDetail(newPlan.plan_id, false);
    app.router.go('detail');
  },

  goBackFromDetail: () => { app.router.go(app.state.isPublicView ? 'public-list' : 'list'); },

  loadPlanEdit: (skipRouting = false) => {
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!plan) return;
    document.getElementById('edit-title').value = plan.title;
    document.getElementById('edit-destination').value = plan.destination;
    document.getElementById('edit-duration').value = plan.days;
    document.getElementById('edit-date').value = plan.start_date;
    const opts = plan.options || {};
    document.getElementById('edit-accommodation').value = opts.accommodation || '';
    document.getElementById('edit-transport').value = opts.transport || '';
    app.state.tempPurposes = [...(opts.purpose || [])];
    app.renderChips('edit');
    if (!skipRouting) app.router.go('plan-edit');
  },
  updatePlanSettings: () => {
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!plan) return;
    plan.title = document.getElementById('edit-title').value;
    plan.destination = document.getElementById('edit-destination').value;
    plan.days = document.getElementById('edit-duration').value;
    plan.start_date = document.getElementById('edit-date').value;
    if (!plan.options) plan.options = {};
    plan.options.accommodation = document.getElementById('edit-accommodation').value;
    plan.options.transport = document.getElementById('edit-transport').value;
    plan.options.purpose = [...app.state.tempPurposes];
    app.saveData();
    app.loadPlanDetail(plan.plan_id, false);
    app.router.go('detail');
  },

  loadWorkspace: () => {
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!plan) return;
    document.getElementById('ws-title').textContent = plan.title;
    document.getElementById('ws-date').textContent = plan.start_date;
    app.renderWorkspaceChecklist();
    const firstTab = document.querySelector('.plan-tabs button');
    if (firstTab) app.switchWorkspaceTab('transit', firstTab);
    app.router.go('workspace');
  },
  switchWorkspaceTab: (tab, btn) => {
    document.querySelectorAll('.plan-tabs button').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    ['transit', 'stay', 'schedule', 'checklist'].forEach(t => {
      const pane = document.getElementById('tab-' + t);
      if (pane) pane.hidden = t !== tab;
    });
  },
  selectCard: (el, type) => {
    el.parentElement.querySelectorAll('.selected').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!plan) return;
    if (!plan.options) plan.options = {};
    if (type === 'transit') plan.options.transport = el.getAttribute('data-name');
    if (type === 'stay') plan.options.accommodation = el.getAttribute('data-name');
    app.saveData();
  },
  saveWorkspace: (nextTab) => {
    if (nextTab) {
      const tabs = document.querySelectorAll('.plan-tabs button');
      let nextBtn;
      tabs.forEach(b => { if (b.getAttribute('onclick').includes(nextTab)) nextBtn = b; });
      if (nextBtn) nextBtn.click();
    } else {
      app.loadPlanDetail(app.state.currentPlanId, false); app.router.go('detail');
    }
  },
  renderWorkspaceChecklist: () => {
    const plan = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!plan) return;
    const container = document.getElementById('checklistContainer');
    if (!container) return;
    container.innerHTML = '';
    plan.checklist = plan.checklist || [];
    plan.checklist.forEach((cat, cIdx) => {
      if (!cat.items) cat.items = [];
      const card = document.createElement('div'); card.className = 'checklist-card';
      const safeTitle = (cat.title || 'カテゴリー').replace(/"/g, '&quot;');
      let html = `<div class="checklist-card__header">
        <input class="category-title-input" type="text" value="${safeTitle}" placeholder="カテゴリー名"
          oninput="app.updateCategoryTitle(${cIdx}, this.value)" />
      </div><div class="checklist-card__body">`;
      cat.items.forEach((item, iIdx) => {
        const qtyVal = item.quantity || '';
        html += `<div class="check-item">
          <input type="checkbox" ${item.is_checked ? 'checked' : ''} onchange="app.toggleCheck(${cIdx}, ${iIdx})">
          <span class="check-item__label">${item.item_name}</span>
          <input class="qty-input" type="text" value="${qtyVal}" placeholder="数量" oninput="app.updateItemQuantity(${cIdx}, ${iIdx}, this.value)">
          <button class="chip__remove" onclick="app.deleteItem(${cIdx}, ${iIdx})">×</button>
        </div>`;
      });
      html += `<div class="add-item-row">
        <input class="item-input" type="text" id="input-${cIdx}" placeholder="アイテム名"
          onkeydown="if(event.key==='Enter'){ event.preventDefault(); app.addItem(${cIdx}); }">
        <input class="qty-input" type="text" id="qty-${cIdx}" placeholder="数量"
          onkeydown="if(event.key==='Enter'){ event.preventDefault(); app.addItem(${cIdx}); }">
        <button type="button" class="add-item-btn" onclick="app.addItem(${cIdx})">＋ アイテムを追加</button>
      </div></div>`;
      card.innerHTML = html;
      container.appendChild(card);
    });
  },
  toggleCheck: (c, i) => {
    const p = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!p) return;
    p.checklist[c].items[i].is_checked = !p.checklist[c].items[i].is_checked;
    app.saveData();
  },
  updateItemQuantity: (c, i, val) => {
    const p = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!p) return;
    p.checklist[c].items[i].quantity = val;
    app.saveData();
  },
  addItem: (c) => {
    const p = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!p) return;
    const input = document.getElementById(`input-${c}`);
    const qtyInput = document.getElementById(`qty-${c}`);
    if (!input) return;
    const val = input.value.trim();
    const qtyVal = qtyInput ? qtyInput.value.trim() : '';
    if (val) {
      if (!p.checklist[c]) p.checklist[c] = { checklist_id: 'cat_' + Date.now(), title: 'カテゴリー', items: [] };
      p.checklist[c].items.push({ checklist_item_id: 'i_' + Date.now(), item_name: val, is_checked: false, quantity: qtyVal });
      app.saveData();
      app.renderWorkspaceChecklist();
      input.value = '';
      if (qtyInput) qtyInput.value = '';
    }
  },
  deleteItem: (c, i) => {
    if (confirm('削除しますか？')) {
      const p = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
      if (!p) return;
      p.checklist[c].items.splice(i, 1); app.saveData(); app.renderWorkspaceChecklist();
    }
  },
  addCategory: () => {
    const p = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!p) return;
    const input = document.getElementById('new-category-name');
    const title = (input?.value || '').trim() || '新しいカテゴリ';
    p.checklist.push({ checklist_id: 'cat_' + Date.now(), title, items: [] });
    if (input) input.value = '';
    app.saveData();
    app.renderWorkspaceChecklist();
  },
  updateCategoryTitle: (c, val) => {
    const p = app.data.plans.find(p => p.plan_id === app.state.currentPlanId);
    if (!p || !p.checklist || !p.checklist[c]) return;
    p.checklist[c].title = val || 'カテゴリー';
    app.saveData();
  },
  saveChecklist: () => { app.saveData(); alert('保存しました'); app.loadPlanDetail(app.state.currentPlanId, false); app.router.go('detail'); },
  toggleProfile: () => { const menu = document.getElementById('profileMenu'); if (menu) menu.hidden = !menu.hidden; }
};

document.addEventListener('DOMContentLoaded', () => {
  app.init();
  document.addEventListener('click', (e) => { if (!e.target.closest('.profile-dropdown')) { const menu = document.getElementById('profileMenu'); if (menu) menu.hidden = true; } });
  const initialView = document.body.dataset.initialView || window.APP_INITIAL_VIEW || 'login';
  const initialPlanId = window.APP_INITIAL_PLAN_ID || '';
  if (initialPlanId) app.state.currentPlanId = initialPlanId;
  if (!app.state.currentPlanId && app.data.plans.length) app.state.currentPlanId = app.data.plans[0].plan_id;
  app.router.go(initialView);
  if (initialView === 'plan-edit') app.loadPlanEdit(true);
  if (initialView === 'list') app.bindSearch('plan-search-input', app.renderPlanList);
  if (initialView === 'public-list') app.bindSearch('public-plan-search-input', app.renderPublicPlanList);
});
