(function createSullivanLibrary(root, factory) {
  const api = factory(root);
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.SullivanLibrary = api;
})(typeof window !== "undefined" ? window : globalThis, (root) => {
  const DB_NAME = "sullivan-ai-local-library";
  const STORE_NAME = "lectures";
  const DB_VERSION = 1;

  function openDatabase() {
    return new Promise((resolve, reject) => {
      if (!root.indexedDB) return reject(new Error("이 브라우저는 강의 로컬 저장소를 지원하지 않습니다."));
      const request = root.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
          store.createIndex("saved_at", "saved_at");
          store.createIndex("title", "title");
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("강의 보관함을 열지 못했습니다."));
    });
  }

  async function runTransaction(mode, operation) {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, mode);
      const store = transaction.objectStore(STORE_NAME);
      let request;
      try { request = operation(store); } catch (error) { db.close(); reject(error); return; }
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("강의 보관함 작업에 실패했습니다."));
      transaction.oncomplete = () => db.close();
      transaction.onerror = () => { db.close(); reject(transaction.error || new Error("강의 보관함 작업에 실패했습니다.")); };
    });
  }

  function save(record) {
    return runTransaction("readwrite", (store) => store.put(record));
  }

  function get(id) {
    return runTransaction("readonly", (store) => store.get(id));
  }

  async function all() {
    const records = await runTransaction("readonly", (store) => store.getAll());
    return records.sort((a, b) => new Date(b.updated_at || b.saved_at) - new Date(a.updated_at || a.saved_at));
  }

  function remove(id) {
    return runTransaction("readwrite", (store) => store.delete(id));
  }

  function summaryText(snapshot = {}) {
    const guide = snapshot.study_guide || {};
    const review = snapshot.review || {};
    const parts = [
      guide.overview,
      ...(review.core_summary || []),
      ...(guide.concept_map || []),
    ].filter(Boolean);
    return parts.length ? parts.join(" ") : "저장된 요약이 없습니다.";
  }

  function normalize(value) {
    return String(value || "").toLowerCase().replace(/[\s·ㆍ.,!?()[\]{}:;/'"_-]+/g, "").trim();
  }

  function findRequested(records = [], command = "") {
    if (!records.length) return null;
    const needle = normalize(command)
      .replace(/저장된|강의|영상|요약|다시|재생|들려줘|듣기|열어줘|열기|최근/g, "");
    if (!needle || normalize(command).includes("최근")) return records[0];
    return records.find((record) => normalize(`${record.title} ${record.subject}`).includes(needle)) || null;
  }

  function requestIntent(command = "") {
    const normalized = normalize(command);
    return normalized.includes("요약") ? "summary" : "open";
  }

  return { DB_NAME, STORE_NAME, save, get, all, remove, summaryText, findRequested, requestIntent };
});
