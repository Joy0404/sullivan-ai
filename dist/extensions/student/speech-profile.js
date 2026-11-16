(function(root){function voiceScore(voice) {
  const lang = String(voice.lang || "").toLowerCase();
  const name = String(voice.name || "").toLowerCase();
  let score = lang === "ko-kr" ? 200 : lang.startsWith("ko") ? 150 : 0;
  if (/natural|neural|online|enhanced|premium|고품질|향상/.test(name)) score += 80;
  if (/sunhi|선히/.test(name)) score += 65;
  if (/google.*한국|google.*korean/.test(name)) score += 55;
  if (/yuna|유나/.test(name)) score += 45;
  if (/heami|혜미/.test(name)) score += 35;
  if (voice.localService) score += 5;
  return score;
}
function prepareSpeechText(text) {
  return String(text || "")
    .replace(/H\s*-\s*R/gi, "에이치 알")
    .replace(/\bTTS\b/gi, "티 티 에스")
    .replace(/\bAI\b/gi, "에이 아이")
    .replace(/1592년/g, "천오백구십이 년")
    .replace(/1597년/g, "천오백구십칠 년")
    .replace(/1598년/g, "천오백구십팔 년")
    .replace(/정명가도/g, "정명 가도")
    .replace(/친명배금/g, "친명 배금")
    .replace(/H-R도/gi, "에이치 알 도")
    .replace(/^\s*1[.)]\s*/gm, "첫째, ")
    .replace(/^\s*2[.)]\s*/gm, "둘째, ")
    .replace(/^\s*3[.)]\s*/gm, "셋째, ")
    .replace(/^\s*4[.)]\s*/gm, "넷째, ")
    .replace(/[→⇒]/g, ", 다음으로, ")
    .replace(/[•·]/g, ", ")
    .replace(/\s*\/\s*/g, " 또는 ")
    .replace(/\n+/g, ". ")
    .replace(/\s+/g, " ")
    .replace(/\.{2,}/g, ".")
    .trim();
}

function speechChunks(text, maxLength = 82) {
  const sentences = prepareSpeechText(text).match(/[^.!?]+[.!?]?/g) || [];
  const chunks = [];
  sentences.forEach((sentence) => {
    const clean = sentence.trim();
    if (clean.length <= maxLength) {
      if (clean) chunks.push(clean);
      return;
    }
    let current = "";
    clean.split(/(?<=,)/).forEach((part) => {
      if (current && `${current} ${part}`.length > maxLength) {
        chunks.push(current.trim());
        current = part;
      } else {
        current = `${current} ${part}`.trim();
      }
    });
    if (current) chunks.push(current.trim());
  });
  return chunks;
}

    function voices(list){return list.filter(v=>String(v.lang).toLowerCase().startsWith('ko')).sort((a,b)=>voiceScore(b)-voiceScore(a));}
    function select(list,uri){const ranked=voices(list);return ranked.find(v=>v.voiceURI===uri)||ranked[0];}
    root.SullivanSpeechProfile={voiceScore,voices,select,prepareSpeechText,speechChunks};
    })(globalThis);
    