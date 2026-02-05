// 持ち物リストのトグルと並び替えを制御するスクリプト

let plan_id;

/**
 * 初期化処理
 */
document.addEventListener('DOMContentLoaded', () => {
  // ページ内の[data-plan-id]属性を持つ要素からプランIDを取得
  const planEl = document.querySelector('[data-plan-id]');
  plan_id = planEl?.getAttribute('data-plan-id');

  const errorLabel = document.querySelector('[data-checklist-toggle-error]')

  const hideError = () => {
    if (errorLabel) errorLabel.hidden = true
  }

  const showError = (message = '保存に失敗しました') => {
    if (!errorLabel) return
    errorLabel.textContent = message
    errorLabel.hidden = false
  }

  // チェック状態の切り替え（PATCHリクエスト）
  document.addEventListener('change', async (event) => {
    const checkbox = event.target.closest('[data-checklist-toggle]')
    if (!checkbox) return
    
    const itemId = checkbox.getAttribute('data-checklist-item-id')
    if (!itemId || itemId.startsWith('guest_')) return

    hideError()
    const nextState = checkbox.checked
    checkbox.disabled = true

    try {
      const response = await fetch(`/plans/checklists/items/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_checked: nextState }),
      })
      const result = await response.json().catch(() => ({}))
      
      if (!response.ok || result.status !== 'success') {
        checkbox.checked = !nextState
        showError();
      } else {
        // 成功したら親ボタンのスタイルを更新
        const btn = checkbox.closest('.item-button');
        if (btn) btn.classList.toggle('checked', nextState);
      }
    } catch (error) {
      console.error('Update Error:', error)
      checkbox.checked = !nextState
      showError()
    } finally {
      checkbox.disabled = false
    }
  })
})

/**
 * ドラッグ開始イベント
 */
function dragStart(event) {
  const target = event.target.closest('.item-button');
  if (!target) return;

  // ドラッグするアイテムのIDを保存
  const id = target.dataset.itemId;
  event.dataTransfer.setData('text/plain', id);
  event.dataTransfer.effectAllowed = 'move';
  
  // ドラッグ中の見た目
  setTimeout(() => target.classList.add('dragging'), 0);
}

/**
 * ドラッグ中（要素の上に乗っている時）
 */
function dragOver(event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = 'move';
  
  const target = event.target.closest('.item-button');
  if (target && !target.classList.contains('dragging')) {
    target.classList.add('drag-over');
  }
}

/**
 * ドラッグ要素が離れた時
 */
function dragLeave(event) {
  const target = event.target.closest('.item-button');
  if (target) target.classList.remove('drag-over');
}

/**
 * ドロップされた時
 */
function drop(event) {
  event.preventDefault();
  const target = event.target.closest('.item-button');
  
  // クラスのクリーンアップ
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
  
  if (target) {
    const draggedId = event.dataTransfer.getData('text/plain');
    const targetId = target.dataset.itemId;

    if (draggedId && targetId && draggedId !== targetId) {
      console.log(`Reordering: ${draggedId} -> ${targetId}`);
      reorderItems(draggedId, targetId);
    }
  }
}

/**
 * ドラッグ終了（ドロップ完了またはキャンセル）
 */
function dragEnd(event) {
  const target = event.target.closest('.item-button');
  if (target) target.classList.remove('dragging');
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
}

/**
 * サーバーへ並び替え順を送信し、DOMを更新する
 */
function reorderItems(draggedId, targetId) {
  if (!plan_id) return;

  fetch(`/plans/${plan_id}/checklist/reorder`, { // /plan/ ではなく /plans/
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dragged_id: draggedId,
      target_id: targetId
    })
  })
  .then(response => {
    if (!response.ok) throw new Error('Network response was not ok');
    return response.json();
  })
  .then(data => {
    if (data.success) {
      const dragged = document.querySelector(`[data-item-id="${draggedId}"]`);
      const target = document.querySelector(`[data-item-id="${targetId}"]`);
      
      if (dragged && target && dragged.parentNode === target.parentNode) {
        const parent = dragged.parentNode;
        // ターゲットの前か後に挿入
        const isAfter = dragged.compareDocumentPosition(target) & Node.DOCUMENT_POSITION_FOLLOWING;
        if (isAfter) {
          parent.insertBefore(dragged, target.nextSibling);
        } else {
          parent.insertBefore(dragged, target);
        }
      }
    } else {
      console.error('Server reported failure in reordering');
    }
  })
  .catch(err => {
    console.error('Reorder error:', err);
    // 失敗した場合はリロードして整合性を取ることも検討
  });
}