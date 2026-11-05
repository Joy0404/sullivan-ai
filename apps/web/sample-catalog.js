/* Shared JSON is the single source for server assignment and client preview. */
window.SullivanSamples = (() => {
  const catalog = {};
  let pending;
  async function load(id) {
    if (!pending) pending = fetch('sample-catalog.json', {cache:'no-store'})
      .then(response => {if (!response.ok) throw Error('샘플 자료를 불러오지 못했습니다. 다시 시도해 주세요.');return response.json();})
      .then(data => {
        Object.assign(catalog, data);
        window.SULLIVAN_SAMPLE_LIBRARY = Object.fromEntries(Object.entries(data).map(([key,value])=>[key,value.snapshot]));
        window.SULLIVAN_SAMPLE_DATA = catalog.science.snapshot;
      }).catch(error => {pending=undefined;throw error;});
    await pending;
    if (!catalog[id]) throw Error('지원하는 샘플을 선택해 주세요.');
    return catalog[id];
  }
  return {catalog,load};
})();
