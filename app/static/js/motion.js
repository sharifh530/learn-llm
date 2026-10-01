/* Native browser motion: no libraries, scroll hijacking, or hidden content. */
const root = document.documentElement;
const reduced = matchMedia("(prefers-reduced-motion: reduce)");
const button = document.querySelector("#motion-toggle");
let preference = "on";
try {preference = localStorage.getItem("tiny-chat-motion") || "on";} catch { /* Optional preference storage. */ }
const active = () => !reduced.matches && preference !== "off";

function applyPreference() {
  const enabled = active();
  root.classList.toggle("motion-off", !enabled);
  button.setAttribute("aria-pressed", String(enabled));
  button.disabled = reduced.matches;
  button.title = reduced.matches ? "Your system requests reduced motion." : "Turn decorative motion on or off";
  document.querySelector("#motion-label").textContent = enabled ? "Motion on" : "Motion off";
  if (!enabled) {
    document.getAnimations().forEach(animation => animation.cancel());
    document.querySelectorAll(".xp-particle").forEach(particle => particle.remove());
  }
}
applyPreference();
button.addEventListener("click", () => {
  preference = active() ? "off" : "on";
  try {localStorage.setItem("tiny-chat-motion", preference);} catch { /* Continue without persistence. */ }
  applyPreference();
});
reduced.addEventListener("change", applyPreference);

function entrance(element, delay = 0, distance = 16) {
  if (!active() || !element || element.hidden) return;
  element.animate([{opacity:.3,transform:`translateY(${distance}px)`},{opacity:1,transform:"translateY(0)"}],
    {duration:500, delay, easing:"cubic-bezier(.2,.75,.25,1)"});
}
document.querySelectorAll(".hero-copy,.experiment-preview,.lesson-header,.lesson-tabs,.page-heading,.chat-aside,.chat-surface,.observatory-heading").forEach((element,index) => entrance(element, Math.min(index * 70,210)));

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    entrance(entry.target, 0, 22);
    observer.unobserve(entry.target);
  });
}, {threshold:.08});
document.querySelectorAll(".progress-strip,.zone-panel,.build-banner,.mission-panel,.workshop-overview,.settings-panel").forEach(element => observer.observe(element));

// Tab changes and newly mounted feedback keep native focus and position.
const panels = document.querySelectorAll(".step-panel,.lab-panel");
const changes = new MutationObserver(records => {
  const targets = new Set();
  records.forEach(record => {
    if (record.type === "attributes" && record.attributeName === "hidden" && !record.target.hidden) targets.add(record.target);
    record.addedNodes.forEach(node => {
      if (node.nodeType !== Node.ELEMENT_NODE) return;
      if (node.matches(".activity-result,.chat-message,.journal-entry")) targets.add(node);
    });
  });
  targets.forEach(element => entrance(element, 0, 8));
});
panels.forEach(panel => changes.observe(panel, {subtree:true,childList:true,attributes:true,attributeFilter:["hidden"]}));
document.querySelectorAll("#chat-messages,[data-journal-entries],#toast").forEach(element => changes.observe(element, {childList:true,attributes:true,attributeFilter:["hidden"]}));
const dialog = document.querySelector("#tutor-dialog");
new MutationObserver(() => {if (dialog.open) entrance(dialog,0,12);}).observe(dialog,{attributes:true,attributeFilter:["open"]});

document.addEventListener("lab:xp", () => {
  if (!active()) return;
  const badge = document.querySelector(".header-progress");
  badge.animate([{transform:"scale(1)"},{transform:"scale(1.13)"},{transform:"scale(1)"}], {duration:500,easing:"ease-out"});
  const rect = badge.getBoundingClientRect();
  for (let index=0; index<10; index++) {
    const particle = document.createElement("span");
    particle.className = "xp-particle";
    particle.setAttribute("aria-hidden","true");
    document.body.append(particle);
    const x = rect.left + rect.width / 2 - (innerWidth - 59);
    const y = rect.top + rect.height / 2 - 61;
    const angle = index * Math.PI * 2 / 10;
    const animation = particle.animate([
      {opacity:1,transform:`translate(${x}px,${y}px) scale(.6)`},
      {opacity:0,transform:`translate(${x + Math.cos(angle)*65}px,${y + Math.sin(angle)*55+15}px) rotate(${index*40}deg) scale(1)`}
    ], {duration:750,easing:"cubic-bezier(.15,.6,.4,1)"});
    animation.finished.then(() => particle.remove()).catch(() => particle.remove());
  }
});

const contents = document.querySelector(".lesson-contents");
if (contents) {
  const narrow = matchMedia("(max-width:760px)");
  const adapt = () => {contents.open = !narrow.matches;};
  adapt(); narrow.addEventListener("change",adapt);
}
