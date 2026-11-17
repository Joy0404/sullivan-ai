// Explicit opt-in local originals. Keys are nonextractable; records are scoped to account + assignment.
async function transaction(mode, action) {
  const db = await new Promise((resolve, reject) => {
    const request = indexedDB.open('sullivan-student-originals', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('originals');
    request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
  });
  return new Promise((resolve, reject) => {
    const tx = db.transaction('originals', mode); const request = action(tx.objectStore('originals'));
    let result; request.onsuccess = () => { result = request.result; };
    tx.oncomplete = () => { db.close(); resolve(result); };
    tx.onabort = tx.onerror = () => { db.close(); reject(tx.error || new Error('로컬 보관 작업에 실패했습니다.')); };
  });
}
export async function saveOriginal(account, lecture, file) {
  if (file.size > 100000000) throw new Error('암호화 보관은 100MB 이하의 파일을 지원합니다. 보관하지 않고 재생할 수 있습니다.');
  const key = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, false, ['encrypt', 'decrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const cipher = await crypto.subtle.encrypt({name: 'AES-GCM', iv}, key, await file.arrayBuffer());
  await transaction('readwrite', store => store.put({key, iv, cipher, type: file.type}, `${account}:${lecture}`));
}
export async function loadOriginal(account, lecture) {
  const record = await transaction('readonly', store => store.get(`${account}:${lecture}`));
  if (!record) throw new Error('이 계정과 강의에 보관한 원본이 없습니다. 파일을 직접 선택하세요.');
  return new Blob([await crypto.subtle.decrypt({name: 'AES-GCM', iv: record.iv}, record.key, record.cipher)], {type: record.type});
}
export async function removeOriginal(account, lecture) {
  await transaction('readwrite', store => store.delete(`${account}:${lecture}`));
}
