/* 城邦地图的 3D 场景（three.js，低多边形风格）。
   这个文件只管「画」和「车怎么开」：不碰 Firebase，也不碰页面上的按钮；
   要显示什么由 main.js 通过 setProjects 传进来，用户点了哪座城、车到了哪座城通过回调告诉 main.js。 */
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { cityPositions, roadPoints, sampleRoad, landDisks, onLand, HUB_RADIUS, hash32, rng, overallProgress, progressOf, stagesOf } from '../core/map.js';

const PER_SEG = 8;                     // 路上每两座城之间的采样点数（和 sampleRoad 的第二个参数一致）
const GROUND_Y = 0.8;                  // 陆地顶面高度
const MAX_SPEED = 26, MAX_REVERSE = 9;

export function webglSupported(){
  try{ const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); }
  catch(e){ return false; }
}

/* ---------- 小工具 ---------- */
function labelSprite(text, {color = '#ffffff', bg = 'rgba(14,22,31,0.78)', size = 46, pad = 18, round = false} = {}){
  const c = document.createElement('canvas'), g = c.getContext('2d');
  g.font = `700 ${size}px Manrope, "PingFang SC", "Microsoft YaHei", sans-serif`;
  const w = Math.ceil(g.measureText(text).width) + pad * 2, h = size + pad;
  c.width = round ? Math.max(w, h) : w; c.height = h;
  g.font = `700 ${size}px Manrope, "PingFang SC", "Microsoft YaHei", sans-serif`;
  g.fillStyle = bg;
  const r = round ? h / 2 : 14;
  g.beginPath(); g.roundRect(0, 0, c.width, c.height, r); g.fill();
  g.fillStyle = color; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text, c.width / 2, c.height / 2 + 2);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map: tex, transparent: true, depthWrite: false, depthTest: false}));
  s.scale.set(c.width / 38, c.height / 38, 1);
  s.renderOrder = 10;
  s.userData.dispose = () => { tex.dispose(); s.material.dispose(); };
  return s;
}

let _glowTex = null;
function glowTexture(){
  if(_glowTex) return _glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d'), grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, 'rgba(255,255,255,1)'); grad.addColorStop(0.35, 'rgba(255,255,255,0.35)'); grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
  _glowTex = new THREE.CanvasTexture(c); _glowTex.colorSpace = THREE.SRGBColorSpace;
  return _glowTex;
}

function stripGeometry(strips, width, y){
  const pos = [], idx = []; let base = 0;
  for(const pts of strips){
    if(pts.length < 2) continue;
    for(let i = 0; i < pts.length; i++){
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      let tx = b.x - a.x, tz = b.z - a.z; const l = Math.hypot(tx, tz) || 1; tx /= l; tz /= l;
      const nx = -tz, nz = tx;
      pos.push(pts[i].x + nx * width / 2, y, pts[i].z + nz * width / 2, pts[i].x - nx * width / 2, y, pts[i].z - nz * width / 2);
    }
    for(let i = 0; i < pts.length - 1; i++){ const a = base + i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    base += pts.length * 2;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  return geo;
}

const mat = (hex, extra = {}) => new THREE.MeshLambertMaterial({color: hex, flatShading: true, ...extra});

/* ---------- 车 ---------- */
function makeCar(colorHex){
  const g = new THREE.Group();
  const c = new THREE.Color(colorHex);
  const body = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.75, 3.6), mat(c)); body.position.y = 0.95;
  const cab = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.7, 1.7), mat(c.clone().offsetHSL(0, -0.1, 0.18))); cab.position.set(0, 1.62, -0.25);
  const glass = new THREE.Mesh(new THREE.BoxGeometry(1.74, 0.42, 1.2), mat(0x1c2a3a)); glass.position.set(0, 1.66, -0.2);
  g.add(body, cab, glass);
  const wGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 10), wMat = mat(0x14181f);
  for(const [x, z] of [[1.05, 1.15], [-1.05, 1.15], [1.05, -1.15], [-1.05, -1.15]]){
    const w = new THREE.Mesh(wGeo, wMat); w.rotation.z = Math.PI / 2; w.position.set(x, 0.5, z); g.add(w);
  }
  const hl = new THREE.MeshBasicMaterial({color: 0xfff0b0});
  for(const x of [-0.7, 0.7]){ const h = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.22, 0.1), hl); h.position.set(x, 1.0, 1.82); g.add(h); }
  g.userData.ring = null;
  return g;
}

/* ---------- 主入口 ---------- */
export function createScene(host, handlers = {}){
  const renderer = new THREE.WebGLRenderer({antialias: true, powerPreference: 'high-performance'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  host.appendChild(renderer.domElement);
  renderer.domElement.style.touchAction = 'none';
  renderer.domElement.style.display = 'block';

  const scene = new THREE.Scene();
  const SKY = 0x18203f;
  scene.background = new THREE.Color(SKY);
  scene.fog = new THREE.FogExp2(SKY, 0.0024);

  const camera = new THREE.PerspectiveCamera(50, 1, 0.5, 3000);
  const hemi = new THREE.HemisphereLight(0x9db2ff, 0x2b3050, 0.75); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffe2b5, 0.6); sun.position.set(-60, 120, 40); scene.add(sun);

  const sea = new THREE.Mesh(new THREE.PlaneGeometry(6000, 6000), mat(0x1f4a78, {flatShading: false}));
  sea.rotation.x = -Math.PI / 2; sea.position.y = -1.4; scene.add(sea);

  const world = new THREE.Group(); scene.add(world);        // 陆地、路、城
  const carsGroup = new THREE.Group(); scene.add(carsGroup);
  const fx = new THREE.Group(); scene.add(fx);               // 粒子
  const hubGroup = buildHub(); scene.add(hubGroup);

  const state = {
    projects: [], selectedId: null,
    built: new Map(),            // projectId -> {sig, group, cities:[{idx,stepId,group,lit,center,tan,pick,title}], samples, points}
    cars: new Map(),             // projectId -> {group, x, z, heading, speed, auto, arrived:Set}
    disks: [], landSig: '', landMeshes: [],
    drive: {x: 0, y: 0}, keys: new Set(),
    cam: {target: new THREE.Vector3(), yaw: 0, pitch: 0.78, dist: 32, userYaw: 0, lastUserT: 0, mode: 'follow', godTarget: new THREE.Vector3(), godDist: 260},
    camGoal: null, particles: [], pulses: [], time: 0, pickMeshes: [], light: 0.55, lightGoal: 0.55,
    running: true, disposed: false,
  };

  /* ---------- 首都 ---------- */
  function buildHub(){
    const g = new THREE.Group();
    const plaza = new THREE.Mesh(new THREE.CylinderGeometry(HUB_RADIUS - 2, HUB_RADIUS - 1, 0.5, 20), mat(0xcfc7b4)); plaza.position.y = GROUND_Y + 0.2; g.add(plaza);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(HUB_RADIUS - 5, 0.28, 6, 40), new THREE.MeshBasicMaterial({color: 0xffd98a})); ring.rotation.x = Math.PI / 2; ring.position.y = GROUND_Y + 0.6; g.add(ring);
    const tower = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2.2, 6, 8), mat(0xe9e1cf)); tower.position.y = GROUND_Y + 3.2; g.add(tower);
    const top = new THREE.Mesh(new THREE.ConeGeometry(2.4, 3, 8), mat(0xb5532f)); top.position.y = GROUND_Y + 7.7; g.add(top);
    const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.8, 8, 6), new THREE.MeshBasicMaterial({color: 0xffe08a})); beacon.position.y = GROUND_Y + 10; g.add(beacon);
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({map: glowTexture(), color: 0xffd98a, transparent: true, opacity: 0.65, blending: THREE.AdditiveBlending, depthWrite: false})); glow.scale.set(20, 20, 1); glow.position.y = GROUND_Y + 9; g.add(glow);
    const r = rng(7);
    for(let i = 0; i < 7; i++){
      const a = i / 7 * Math.PI * 2 + 0.3, rad = HUB_RADIUS - 6.5;
      const w = 2 + r() * 1.4, h = 2.6 + r() * 3;
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), mat(i % 2 ? 0xd8cdb4 : 0xc9bfa6)); b.position.set(Math.cos(a) * rad, GROUND_Y + h / 2 + 0.4, Math.sin(a) * rad); g.add(b);
      const roof = new THREE.Mesh(new THREE.ConeGeometry(w * 0.78, 1.3, 4), mat(0x8a4a33)); roof.rotation.y = Math.PI / 4; roof.position.set(b.position.x, GROUND_Y + h + 1.05, b.position.z); g.add(roof);
      const win = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.6, 0.06), new THREE.MeshBasicMaterial({color: 0xffe08a})); win.position.set(b.position.x, GROUND_Y + h * 0.55, b.position.z + w / 2 + 0.03); g.add(win);
    }
    const label = labelSprite('首都', {size: 30}); label.position.set(0, GROUND_Y + 11, 0); g.add(label);
    return g;
  }

  /* ---------- 陆地 ---------- */
  function rebuildLand(){
    const roads = [];
    for(const b of state.built.values()) roads.push(b.points);
    state.disks = landDisks(roads);
    const sig = state.disks.length + ':' + state.disks.map(d => (d.x | 0) + ',' + (d.z | 0)).join(';');
    if(sig === state.landSig) return;
    state.landSig = sig;
    state.landMeshes.forEach(m => { world.remove(m); m.geometry.dispose(); m.material.dispose(); });
    state.landMeshes = [];
    const N = state.disks.length;
    const grass = new THREE.InstancedMesh(new THREE.CylinderGeometry(1, 1, 2, 10), mat(0xffffff), N);
    const sand = new THREE.InstancedMesh(new THREE.CylinderGeometry(1, 1, 2, 10), mat(0xffffff), N);
    const m4 = new THREE.Matrix4(), col = new THREE.Color();
    state.disks.forEach((d, i) => {
      const r = rng(hash32('d' + i));
      const top = GROUND_Y + (i % 7) * 0.012;
      m4.compose(new THREE.Vector3(d.x, top - 1, d.z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), r() * 3), new THREE.Vector3(d.r, 1, d.r));
      grass.setMatrixAt(i, m4);
      grass.setColorAt(i, col.setHSL(0.30 + r() * 0.03, 0.34, 0.34 + r() * 0.05));
      m4.compose(new THREE.Vector3(d.x, GROUND_Y - 1.25 - (i % 5) * 0.01, d.z), new THREE.Quaternion(), new THREE.Vector3(d.r + 2.6, 1, d.r + 2.6));
      sand.setMatrixAt(i, m4);
      sand.setColorAt(i, col.set(0xcdb98a));
    });
    grass.instanceMatrix.needsUpdate = sand.instanceMatrix.needsUpdate = true;
    grass.instanceColor.needsUpdate = sand.instanceColor.needsUpdate = true;
    world.add(grass, sand); state.landMeshes.push(grass, sand);
  }

  /* ---------- 一个项目：路 + 城 ---------- */
  const sigOf = p => [p.slot, p.color, p.title, p.steps.map(s => s.id + ':' + (s.doneAt ? 1 : 0) + ':' + s.title + ':' + (s.stage || '')).join('|')].join('#');

  function disposeGroup(g){
    g.traverse(o => {
      if(o.userData && o.userData.dispose) o.userData.dispose();
      if(o.geometry) o.geometry.dispose();
      if(o.material && !o.userData.shared){ (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose()); }
    });
  }

  /* 每座城除了几间房子，还有一个按「阶段」换花样的地标：0 民居 · 1 工坊 · 2 塔楼 · 3 圆顶剧场 · 4 集市；最后一座城是金顶大塔 */
  function addLandmark(g, kind, isLast, lit, color, r, px, pz, yaw){
    const grp = new THREE.Group(); grp.position.set(px, GROUND_Y, pz); grp.rotation.y = yaw;
    const wall = lit ? new THREE.Color(0xf0e2c4) : new THREE.Color(0x3c4358);
    const accent = lit ? color.clone() : new THREE.Color(0x4a5268);
    const gold = lit ? new THREE.Color(0xf2c14e) : new THREE.Color(0x5a5f70);
    const win = new THREE.MeshBasicMaterial({color: 0xffe08a});
    const add = (geo, m, x, y, z) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); grp.add(o); return o; };
    const shadow = new THREE.Mesh(new THREE.CircleGeometry(4.2, 12), new THREE.MeshBasicMaterial({color: 0x000000, transparent: true, opacity: 0.22, depthWrite: false})); shadow.rotation.x = -Math.PI / 2; shadow.position.y = 0.05; grp.add(shadow);
    if(isLast){
      add(new THREE.CylinderGeometry(3.4, 3.8, 1.2, 8), mat(wall), 0, 0.6, 0);
      add(new THREE.CylinderGeometry(2.1, 2.7, 7, 8), mat(wall), 0, 4.7, 0);
      add(new THREE.CylinderGeometry(2.6, 2.1, 1.0, 8), mat(accent), 0, 8.7, 0);
      add(new THREE.ConeGeometry(2.4, 4.6, 8), mat(gold), 0, 11.5, 0);
      add(new THREE.SphereGeometry(0.55, 8, 6), new THREE.MeshBasicMaterial({color: lit ? 0xfff0b0 : 0x666b7c}), 0, 14.2, 0);
      if(lit) for(let a = 0; a < 6; a++) add(new THREE.BoxGeometry(0.5, 0.9, 0.12), win, Math.cos(a * 1.047) * 2.45, 3 + (a % 2) * 2, Math.sin(a * 1.047) * 2.45).rotation.y = -a * 1.047;
    } else if(kind === 1){            // 工坊：长屋 + 烟囱 + 齿轮
      add(new THREE.BoxGeometry(5.6, 2.6, 3), mat(wall), 0, 1.3, 0);
      const roof = add(new THREE.CylinderGeometry(2.2, 2.2, 5.9, 3), mat(accent), 0, 3.1, 0); roof.rotation.set(0, 0, Math.PI / 2);
      add(new THREE.BoxGeometry(0.9, 3.4, 0.9), mat(0x7a5a4a), 1.8, 3.8, 0.6);
      const gear = add(new THREE.TorusGeometry(0.9, 0.28, 5, 8), mat(gold), -2.4, 1.6, 1.6); gear.rotation.y = 0;
      if(lit) for(let k = -2; k <= 2; k += 2) add(new THREE.BoxGeometry(0.6, 0.7, 0.1), win, k, 1.4, 1.55);
    } else if(kind === 2){            // 塔楼
      add(new THREE.CylinderGeometry(1.7, 2.2, 6.5, 8), mat(wall), 0, 3.25, 0);
      add(new THREE.CylinderGeometry(2.2, 1.7, 0.8, 8), mat(accent), 0, 6.9, 0);
      add(new THREE.ConeGeometry(2.0, 3.6, 8), mat(accent), 0, 9.1, 0);
      if(lit) for(let a = 0; a < 5; a++) add(new THREE.BoxGeometry(0.4, 0.8, 0.1), win, Math.cos(a * 1.257) * 1.85, 2 + (a % 2) * 2.2, Math.sin(a * 1.257) * 1.85).rotation.y = -a * 1.257;
    } else if(kind === 3){            // 圆顶剧场
      add(new THREE.CylinderGeometry(3.0, 3.2, 2.2, 10), mat(wall), 0, 1.1, 0);
      add(new THREE.SphereGeometry(3.0, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(accent), 0, 2.2, 0);
      for(let a = 0; a < 6; a++) add(new THREE.CylinderGeometry(0.22, 0.22, 2.4, 5), mat(0xe8dfc9), Math.cos(a * 1.047) * 3.35, 1.2, Math.sin(a * 1.047) * 3.35);
      add(new THREE.SphereGeometry(0.4, 6, 5), mat(gold), 0, 5.4, 0);
    } else if(kind === 4){            // 集市：围成一圈的摊位 + 中间喷泉
      add(new THREE.CylinderGeometry(0.9, 1.1, 0.9, 8), mat(0xb9c4d4), 0, 0.45, 0);
      add(new THREE.SphereGeometry(0.45, 6, 5), new THREE.MeshBasicMaterial({color: lit ? 0x8fd3ff : 0x59617a}), 0, 1.2, 0);
      for(let a = 0; a < 4; a++){
        const x = Math.cos(a * 1.571 + 0.4) * 3.0, z = Math.sin(a * 1.571 + 0.4) * 3.0;
        add(new THREE.BoxGeometry(1.5, 1.0, 1.0), mat(wall), x, 0.5, z).rotation.y = -(a * 1.571 + 0.4);
        const aw = add(new THREE.ConeGeometry(1.3, 1.0, 4), mat(a % 2 ? accent : (lit ? new THREE.Color(0xe36b5a) : new THREE.Color(0x4a5268))), x, 1.8, z); aw.rotation.y = Math.PI / 4;
      }
    }
    g.add(grp);
  }

  function makeCity(project, step, idx, center, tan, lit, kind = 0, isLast = false){
    const color = new THREE.Color(project.color);
    const r = rng(hash32(project.id + ':' + step.id));
    const g = new THREE.Group(); g.position.set(center.x, 0, center.z);
    const nrm = {x: -tan.z, z: tan.x};
    const yaw = Math.atan2(tan.x, tan.z);

    const plaza = new THREE.Mesh(new THREE.CylinderGeometry(4.7, 5.1, 0.45, 9), mat(lit ? 0xe3d9c2 : 0x6f7688)); plaza.position.y = GROUND_Y + 0.15; g.add(plaza);
    const landSide = r() < 0.5 ? 1 : -1;
    const nb = kind === 0 ? 3 + Math.floor(r() * 2) : 2;
    const palette = [color.clone(), color.clone().offsetHSL(0.05, -0.05, 0.1), new THREE.Color(0xf0e2c4), color.clone().offsetHSL(-0.05, -0.1, -0.08)];
    for(let k = 0; k < nb; k++){
      const side = kind === 0 ? (k % 2 ? 1 : -1) : -landSide;
      const along = (r() - 0.5) * 7, lat = side * (4.2 + r() * 2.2);
      const w = 1.7 + r() * 1.0, d = 1.7 + r() * 1.0, h = 2.2 + r() * 3.4;
      const b = new THREE.Group(); b.position.set(tan.x * along + nrm.x * lat, GROUND_Y, tan.z * along + nrm.z * lat); b.rotation.y = yaw;
      const wall = lit ? palette[Math.floor(r() * palette.length)] : new THREE.Color().setHSL(0.62, 0.14, 0.26 + r() * 0.06);
      const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(wall)); body.position.y = h / 2; b.add(body);
      const roof = new THREE.Mesh(new THREE.ConeGeometry(Math.max(w, d) * 0.78, 1.5, 4), mat(lit ? wall.clone().offsetHSL(0, 0.1, -0.22) : 0x2f3545)); roof.rotation.y = Math.PI / 4; roof.position.y = h + 0.7; b.add(roof);
      const shadow = new THREE.Mesh(new THREE.CircleGeometry(Math.max(w, d) * 1.05, 10), new THREE.MeshBasicMaterial({color: 0x000000, transparent: true, opacity: 0.22, depthWrite: false})); shadow.rotation.x = -Math.PI / 2; shadow.position.y = 0.05; b.add(shadow);
      if(lit){
        const wm = new THREE.MeshBasicMaterial({color: 0xffe08a});
        const rows = Math.max(1, Math.floor(h / 1.5));
        for(let ry = 0; ry < rows; ry++) for(const wz of [-d * 0.22, d * 0.22]){
          if(r() < 0.25) continue;
          const win = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.5, 0.4), wm); win.position.set(side * (w / 2 + 0.03), 1.0 + ry * 1.4, wz); b.add(win);
        }
      }
      g.add(b);
    }
    if(kind !== 0 || isLast) addLandmark(g, kind, isLast, lit, color, r, nrm.x * landSide * 6.8, nrm.z * landSide * 6.8, yaw);
    for(let k = 0; k < 3 + Math.floor(r() * 3); k++){
      const side = r() < 0.5 ? 1 : -1, along = (r() - 0.5) * 9, lat = side * (8 + r() * 3);
      const tx = tan.x * along + nrm.x * lat, tz = tan.z * along + nrm.z * lat;
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.28, 1.1, 5), mat(0x5a3d2a)); trunk.position.set(tx, GROUND_Y + 0.55, tz);
      const top = new THREE.Mesh(new THREE.ConeGeometry(1.1 + r() * 0.5, 2.6, 6), mat(lit ? 0x3f8d4a : 0x2c4a45)); top.position.set(tx, GROUND_Y + 2.2, tz);
      g.add(trunk, top);
    }
    const flagPole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 7.5, 5), mat(0xcfd6e0)); flagPole.position.set(nrm.x * 3, GROUND_Y + 3.75, nrm.z * 3);
    const flag = new THREE.Mesh(new THREE.BoxGeometry(1.7, 1.0, 0.06), new THREE.MeshBasicMaterial({color: lit ? color : 0x596175})); flag.position.set(nrm.x * 3 + tan.x * 0.9, GROUND_Y + 7.0, nrm.z * 3 + tan.z * 0.9); flag.rotation.y = yaw;
    g.add(flagPole, flag);
    if(lit){
      const glow = new THREE.Sprite(new THREE.SpriteMaterial({map: glowTexture(), color: color.clone().lerp(new THREE.Color(0xffd98a), 0.5), transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false}));
      glow.scale.set(26, 26, 1); glow.position.y = GROUND_Y + 4; g.add(glow);
    }
    const num = labelSprite(String(idx + 1), {round: true, size: 40, bg: lit ? project.color : 'rgba(70,78,98,0.92)', color: '#fff', pad: 14});
    num.position.set(0, GROUND_Y + 10.4, 0); g.add(num);

    const pick = new THREE.Mesh(new THREE.SphereGeometry(7, 8, 6), new THREE.MeshBasicMaterial({transparent: true, opacity: 0, depthWrite: false}));
    pick.position.set(center.x, GROUND_Y + 3, center.z); pick.userData.city = {projectId: project.id, idx};
    return {group: g, pick, lit, title: null, num};
  }

  function buildProject(project){
    const group = new THREE.Group();
    const n = project.steps.length;
    const pts = roadPoints(project.slot, project.id, n);
    const samples = sampleRoad(pts, PER_SEG);
    const cityPts = pts.slice(1);
    // 路：沥青 + 中线（做过的路段用项目色，没做的是灰色）
    const asphalt = new THREE.Mesh(stripGeometry([samples], 3.8, GROUND_Y + 0.08), new THREE.MeshBasicMaterial({color: 0x2c3240, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1}));
    group.add(asphalt);
    const litStrips = [], dimStrips = [];
    for(let j = 0; j < n; j++){
      const seg = samples.slice(j * PER_SEG, (j + 1) * PER_SEG + 1);
      (project.steps[j].doneAt ? litStrips : dimStrips).push(seg);
    }
    group.add(new THREE.Mesh(stripGeometry(dimStrips, 0.45, GROUND_Y + 0.13), new THREE.MeshBasicMaterial({color: 0x5b6477, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2})));
    group.add(new THREE.Mesh(stripGeometry(litStrips, 0.7, GROUND_Y + 0.14), new THREE.MeshBasicMaterial({color: new THREE.Color(project.color), side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -3})));
    const cities = [];
    const kindOf = [];
    stagesOf(project.steps).forEach((st, si) => st.idx.forEach((ix, k) => { kindOf[ix] = (si * 2 + k) % 5; }));
    for(let i = 0; i < n; i++){
      const prev = pts[i], next = pts[i + 2] || {x: cityPts[i].x * 2 - pts[i + 1 - 1].x, z: cityPts[i].z * 2 - pts[i].z};
      let tx = next.x - prev.x, tz = next.z - prev.z; const l = Math.hypot(tx, tz) || 1; tx /= l; tz /= l;
      const lit = !!project.steps[i].doneAt;
      const c = makeCity(project, project.steps[i], i, cityPts[i], {x: tx, z: tz}, lit, kindOf[i] || 0, n > 1 && i === n - 1);
      group.add(c.group); group.add(c.pick);
      cities.push({idx: i, stepId: project.steps[i].id, center: cityPts[i], tan: {x: tx, z: tz}, ...c});
    }
    return {sig: sigOf(project), group, cities, samples, points: pts};
  }

  function setProjects(projects, selectedId){
    const prevDone = new Map();
    for(const [pid, b] of state.built) prevDone.set(pid, new Set(b.cities.filter(c => c.lit).map(c => c.stepId)));
    state.projects = projects; if(selectedId !== undefined) state.selectedId = selectedId;
    const ids = new Set(projects.map(p => p.id));
    for(const [pid, b] of [...state.built]) if(!ids.has(pid)){ world.remove(b.group); disposeGroup(b.group); state.built.delete(pid); const c = state.cars.get(pid); if(c){ carsGroup.remove(c.group); disposeGroup(c.group); state.cars.delete(pid); } }
    let landDirty = false;
    for(const p of projects){
      const old = state.built.get(p.id);
      if(old && old.sig === sigOf(p)) continue;
      if(old){ world.remove(old.group); disposeGroup(old.group); }
      const b = buildProject(p); world.add(b.group); state.built.set(p.id, b); landDirty = true;
      // 新点亮的城：弹一下 + 撒粒子
      const was = prevDone.get(p.id);
      if(was) for(const c of b.cities) if(c.lit && !was.has(c.stepId)) popCity(p, c);
      if(!state.cars.has(p.id)) addCar(p, b);
      else state.cars.get(p.id).group.children[0].material.color.set(p.color);
    }
    if(landDirty) rebuildLand();
    state.lightGoal = 0.55 + 0.7 * overallProgress(projects);
    updateGodTarget();
    updateMarkers();
  }

  /* ---------- 「下一站」标记：箭头 + 光圈，选中项目的还有一道光柱 ---------- */
  const marker = new THREE.Group(); scene.add(marker);
  function updateMarkers(){
    while(marker.children.length){ const o = marker.children.pop(); disposeGroup(o); }
    state.pulses = [];
    for(const p of state.projects){
      if(p.parked) continue;
      const b = state.built.get(p.id); const gr = progressOf(p);
      if(!b || gr.nextIndex < 0) continue;
      const c = b.cities[gr.nextIndex], sel = p.id === state.selectedId, color = new THREE.Color(p.color);
      const g = new THREE.Group(); g.position.set(c.center.x, GROUND_Y, c.center.z);
      const ring = new THREE.Mesh(new THREE.RingGeometry(5.6, 6.5, 40), new THREE.MeshBasicMaterial({color, transparent: true, opacity: sel ? 0.95 : 0.5, side: THREE.DoubleSide, depthWrite: false})); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.35; g.add(ring);
      const arrow = new THREE.Mesh(new THREE.ConeGeometry(1.5, 3, 4), new THREE.MeshBasicMaterial({color})); arrow.rotation.x = Math.PI; arrow.position.y = 14; g.add(arrow);
      if(sel){
        const beam = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 3.2, 38, 12, 1, true), new THREE.MeshBasicMaterial({color, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide})); beam.position.y = 19; g.add(beam);
      }
      marker.add(g); state.pulses.push({ring, arrow, baseY: 14, sel});
    }
  }

  /* ---------- 点亮动画 ---------- */
  function popCity(project, c){
    c.group.scale.setScalar(0.5); c.group.userData.pop = 0;
    const col = new THREE.Color(project.color);
    for(let i = 0; i < 26; i++){
      const m = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 0.5), new THREE.MeshBasicMaterial({color: i % 3 ? col : new THREE.Color(0xffe08a), transparent: true}));
      m.position.set(c.center.x, GROUND_Y + 4, c.center.z);
      const a = Math.random() * Math.PI * 2, s = 6 + Math.random() * 10;
      state.particles.push({m, vx: Math.cos(a) * s, vz: Math.sin(a) * s, vy: 12 + Math.random() * 10, life: 1.3});
      fx.add(m);
    }
    state.popping = state.popping || []; state.popping.push(c);
  }

  /* ---------- 车 ---------- */
  function carStart(project, b){
    const gr = progressOf(project);
    const from = gr.nextIndex <= 0 ? b.points[0] : b.cities[gr.nextIndex - 1].center;
    const toC = b.cities[Math.max(0, gr.nextIndex < 0 ? b.cities.length - 1 : gr.nextIndex)];
    const to = toC ? toC.center : {x: from.x + 1, z: from.z};
    const h = Math.atan2(to.x - from.x, to.z - from.z);
    return {x: from.x + Math.sin(h) * 3, z: from.z + Math.cos(h) * 3, heading: h};
  }
  function addCar(project, b){
    const s = carStart(project, b);
    const g = makeCar(project.color); carsGroup.add(g);
    state.cars.set(project.id, {group: g, ...s, speed: 0, auto: null, arrived: new Set()});
  }
  function selCar(){ return state.cars.get(state.selectedId) || null; }

  function stepCar(car, dt, isSel){
    if(car.auto){                       // 自动开向目标城
      const a = car.auto;
      const tgt = a.path[a.i];
      const dx = tgt.x - car.x, dz = tgt.z - car.z, d = Math.hypot(dx, dz);
      const sp = 34 * dt;
      if(d <= sp){ car.x = tgt.x; car.z = tgt.z; a.i++; if(a.i >= a.path.length){ car.auto = null; car.speed = 0; if(a.done) a.done(); } }
      else { car.x += dx / d * sp; car.z += dz / d * sp; const th = Math.atan2(dx, dz); let dh = th - car.heading; dh = Math.atan2(Math.sin(dh), Math.cos(dh)); car.heading += dh * Math.min(1, dt * 10); car.speed = 34; }
    } else if(isSel){
      const kx = (state.keys.has('ArrowRight') || state.keys.has('KeyD') ? 1 : 0) - (state.keys.has('ArrowLeft') || state.keys.has('KeyA') ? 1 : 0);
      const ky = (state.keys.has('ArrowUp') || state.keys.has('KeyW') ? 1 : 0) - (state.keys.has('ArrowDown') || state.keys.has('KeyS') ? 1 : 0);
      const ix = Math.abs(state.drive.x) > Math.abs(kx) ? state.drive.x : kx, iy = Math.abs(state.drive.y) > Math.abs(ky) ? state.drive.y : ky;
      const target = iy >= 0 ? iy * MAX_SPEED : iy * MAX_REVERSE;
      const rate = Math.abs(target) < Math.abs(car.speed) && Math.sign(target) === Math.sign(car.speed) ? 22 : (target === 0 ? 26 : 40);
      const dv = target - car.speed; car.speed += Math.max(-rate * dt, Math.min(rate * dt, dv));
      car.heading -= ix * 2.1 * dt * Math.min(1, Math.abs(car.speed) / 7) * (car.speed >= 0 ? 1 : -1);
      const nx = car.x + Math.sin(car.heading) * car.speed * dt, nz = car.z + Math.cos(car.heading) * car.speed * dt;
      if(onLand(state.disks, nx, nz)){ car.x = nx; car.z = nz; }
      else if(onLand(state.disks, nx, car.z)){ car.x = nx; car.speed *= 0.9; }
      else if(onLand(state.disks, car.x, nz)){ car.z = nz; car.speed *= 0.9; }
      else car.speed *= -0.25;
    } else { car.speed = 0; }
    car.group.position.set(car.x, GROUND_Y + 0.05, car.z);
    car.group.rotation.y = car.heading;
    if(isSel) car.group.position.y += Math.sin(state.time * 18) * 0.02 * Math.min(1, Math.abs(car.speed) / 10);
  }

  function checkArrival(){
    const car = selCar(); if(!car) return;
    const b = state.built.get(state.selectedId); if(!b) return;
    for(const c of b.cities){
      const d = Math.hypot(car.x - c.center.x, car.z - c.center.z);
      if(d < 5.2 && !car.arrived.has(c.idx)){ car.arrived.add(c.idx); if(handlers.onArrive) handlers.onArrive(state.selectedId, c.idx); }
      else if(d > 11) car.arrived.delete(c.idx);
    }
  }

  /* 自动开到某座城：沿路的采样点走过去（没在路上就先直线到最近的路点） */
  function driveTo(projectId, idx, done){
    const b = state.built.get(projectId), car = state.cars.get(projectId); if(!b || !car || !b.cities[idx]) return;
    state.selectedId = projectId;
    let ni = 0, nd = Infinity;
    b.samples.forEach((s, i) => { const d = Math.hypot(s.x - car.x, s.z - car.z); if(d < nd){ nd = d; ni = i; } });
    const targetI = (idx + 1) * PER_SEG;           // 第 idx 座城在路的采样点里的下标（0 是起点）
    const path = [];
    const step = ni <= targetI ? 1 : -1;
    for(let i = ni; step > 0 ? i <= targetI : i >= targetI; i += step) path.push(b.samples[i]);
    const c = b.cities[idx].center;
    path.push({x: c.x, z: c.z});
    car.arrived.delete(idx);
    car.auto = {path, i: 0, done: () => { const was = car.arrived.has(idx); car.arrived.add(idx); if(!was && handlers.onArrive) handlers.onArrive(projectId, idx); if(done) done(); }};
    state.cam.mode = 'follow';
  }

  /* ---------- 相机 ---------- */
  function updateGodTarget(){
    let mx = 0, mz = 0, n = 0, maxR = 40;
    for(const b of state.built.values()) for(const c of b.cities){ mx += c.center.x; mz += c.center.z; n++; maxR = Math.max(maxR, Math.hypot(c.center.x, c.center.z)); }
    state.cam.godTarget.set(n ? mx / n * 0.6 : 0, 0, n ? mz / n * 0.6 : 0);
    state.cam.godDist = Math.min(900, 70 + maxR * 1.5);
  }
  function setView(mode){
    const c = state.cam;
    if(mode === 'god'){ c.mode = 'god'; c.goal = {pitch: 1.12, dist: c.godDist}; }
    else { c.mode = 'follow'; c.goal = {pitch: 0.78, dist: 32}; c.userYaw = 0; }
  }
  function updateCamera(dt){
    const c = state.cam, car = selCar();
    if(c.goal){
      const k = 1 - Math.exp(-4 * dt);
      c.pitch += (c.goal.pitch - c.pitch) * k; c.dist += (c.goal.dist - c.dist) * k;
      if(Math.abs(c.pitch - c.goal.pitch) < 0.004 && Math.abs(c.dist - c.goal.dist) < 0.5) c.goal = null;
    }
    let tx, tz, yaw;
    if(c.mode === 'follow' && car){
      tx = car.x; tz = car.z;
      if(state.time - c.lastUserT > 2.2 && Math.abs(car.speed) > 2) c.userYaw *= Math.exp(-1.6 * dt);
      yaw = car.heading + Math.PI + c.userYaw;
      c.target.x += (tx - c.target.x) * (1 - Math.exp(-7 * dt)); c.target.z += (tz - c.target.z) * (1 - Math.exp(-7 * dt)); c.target.y = 1.2;
    } else {
      tx = c.godTarget.x; tz = c.godTarget.z; yaw = c.userYaw;
      if(!c.panned){ c.target.x += (tx - c.target.x) * (1 - Math.exp(-4 * dt)); c.target.z += (tz - c.target.z) * (1 - Math.exp(-4 * dt)); }
      c.target.y = 0;
    }
    const cp = Math.cos(c.pitch);
    camera.position.set(c.target.x + Math.sin(yaw) * cp * c.dist, c.target.y + Math.sin(c.pitch) * c.dist, c.target.z + Math.cos(yaw) * cp * c.dist);
    camera.lookAt(c.target);
  }

  /* ---------- 输入：拖动旋转、滚轮 / 双指缩放、点城 ---------- */
  const el = renderer.domElement;
  const ptrs = new Map(); let down = null; let pinch = 0;
  const raycaster = new THREE.Raycaster(), ndc = new THREE.Vector2();
  el.addEventListener('pointerdown', e => {
    el.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, {x: e.clientX, y: e.clientY});
    down = ptrs.size === 1 ? {x: e.clientX, y: e.clientY, t: performance.now(), moved: 0} : null;
    if(ptrs.size === 2){ const [a, b] = [...ptrs.values()]; pinch = Math.hypot(a.x - b.x, a.y - b.y); }
    if(state.cam.goal) state.cam.goal = null;
  });
  el.addEventListener('pointermove', e => {
    const p = ptrs.get(e.pointerId); if(!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    const c = state.cam;
    if(ptrs.size === 1){
      if(down) down.moved += Math.abs(dx) + Math.abs(dy);
      c.userYaw -= dx * 0.0065; c.pitch = Math.max(0.12, Math.min(1.45, c.pitch + dy * 0.0055)); c.lastUserT = state.time;
    } else if(ptrs.size === 2){
      const [a, b] = [...ptrs.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y);
      if(pinch) c.dist = Math.max(14, Math.min(1400, c.dist * (pinch / d)));
      pinch = d; c.lastUserT = state.time;
      if(c.mode === 'god'){ const k = c.dist * 0.0016; c.panned = true; c.target.x -= (Math.cos(c.userYaw) * dx + Math.sin(c.userYaw) * dy) * k * 0.5; c.target.z += (Math.sin(c.userYaw) * dx - Math.cos(c.userYaw) * dy) * k * 0.5; }
    }
  });
  const end = e => {
    const wasClick = down && ptrs.size === 1 && down.moved < 7 && performance.now() - down.t < 450;
    ptrs.delete(e.pointerId); if(ptrs.size < 2) pinch = 0;
    if(wasClick){
      const r = el.getBoundingClientRect();
      ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      raycaster.setFromCamera(ndc, camera);
      const picks = []; for(const b of state.built.values()) for(const c of b.cities) picks.push(c.pick);
      const hit = raycaster.intersectObjects(picks, false)[0];
      if(hit && handlers.onCityClick) handlers.onCityClick(hit.object.userData.city.projectId, hit.object.userData.city.idx);
    }
    down = null;
  };
  el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
  el.addEventListener('wheel', e => { e.preventDefault(); const c = state.cam; c.dist = Math.max(14, Math.min(1400, c.dist * Math.exp(e.deltaY * 0.0012))); c.goal = null; }, {passive: false});
  const typing = () => { const a = document.activeElement; return !!a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) && a.offsetParent !== null; };   // 输入框藏起来（比如新建项目的弹窗关了）就不算在打字
  const kd = e => { if(typing()) return; if(/^(Arrow|Key[WASD])/.test(e.code)){ state.keys.add(e.code); if(car_auto_cancel()) e.preventDefault(); if(e.code.startsWith('Arrow')) e.preventDefault(); } };
  const ku = e => state.keys.delete(e.code);
  const car_auto_cancel = () => { const c = selCar(); if(c && c.auto){ c.auto = null; } return false; };
  window.addEventListener('keydown', kd); window.addEventListener('keyup', ku); window.addEventListener('blur', () => state.keys.clear());

  /* ---------- 循环 ---------- */
  function resize(){
    const w = host.clientWidth || 300, h = host.clientHeight || 300;
    renderer.setSize(w, h, false); el.style.width = '100%'; el.style.height = '100%';
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize); ro.observe(host); resize();

  let last = performance.now(), raf = 0;
  function frame(now){
    if(state.disposed) return;
    raf = requestAnimationFrame(frame);
    if(document.hidden){ last = now; return; }
    const dt = Math.min(0.05, (now - last) / 1000); last = now; state.time += dt;
    if(state.drive.x || state.drive.y){ const c = selCar(); if(c && c.auto) c.auto = null; }
    for(const [pid, car] of state.cars) stepCar(car, dt, pid === state.selectedId);
    checkArrival();
    updateCamera(dt);
    // 环境光：点亮的城越多，整个世界越亮
    state.light += (state.lightGoal - state.light) * (1 - Math.exp(-2 * dt));
    hemi.intensity = state.light; sun.intensity = 0.3 + (state.light - 0.55) * 0.9;
    // 标记动画
    for(const p of state.pulses){ p.arrow.position.y = p.baseY + Math.sin(state.time * 3) * 0.8; p.arrow.rotation.y += dt * 2; p.ring.scale.setScalar(1 + Math.sin(state.time * 3) * 0.06); }
    // 弹出的城
    if(state.popping){ state.popping = state.popping.filter(c => { const t = (c.group.userData.pop += dt) / 0.7; const e = t >= 1 ? 1 : 1 + 0.35 * Math.sin(t * Math.PI) * (1 - t) * 2 - (1 - t) * (1 - t) * 0.5; c.group.scale.setScalar(Math.max(0.3, e)); if(t >= 1){ c.group.scale.setScalar(1); return false; } return true; }); }
    // 粒子
    state.particles = state.particles.filter(p => { p.life -= dt; p.vy -= 24 * dt; p.m.position.x += p.vx * dt; p.m.position.z += p.vz * dt; p.m.position.y += p.vy * dt; p.m.rotation.x += dt * 5; p.m.material.opacity = Math.max(0, p.life / 1.3); if(p.life <= 0 || p.m.position.y < GROUND_Y){ fx.remove(p.m); p.m.geometry.dispose(); p.m.material.dispose(); return false; } return true; });
    // 城的名字：下一站、离车近的显示
    const car = selCar(), selB = state.built.get(state.selectedId), selP = state.projects.find(p => p.id === state.selectedId);
    if(selB && selP){
      const nx = progressOf(selP).nextIndex;
      for(const c of selB.cities){
        const near = car && Math.hypot(car.x - c.center.x, car.z - c.center.z) < 26;
        const show = near || c.idx === nx;
        if(show && !c.title){ c.title = labelSprite(selP.steps[c.idx].title.slice(0, 18), {size: 34, pad: 14}); c.title.position.set(0, GROUND_Y + 12.6, 0); c.group.add(c.title); }
        if(c.title) c.title.visible = show;
      }
    }
    renderer.render(scene, camera);
  }
  raf = requestAnimationFrame(frame);

  return {
    setProjects, driveTo, setView,
    select(pid){ state.selectedId = pid; state.cam.mode = state.cam.mode === 'god' ? 'god' : 'follow'; updateMarkers(); },
    setDrive(x, y){ state.drive.x = x; state.drive.y = y; },
    get view(){ return state.cam.mode; },
    carNear(pid, idx){ const b = state.built.get(pid), c = state.cars.get(pid); if(!b || !c || !b.cities[idx]) return false; return Math.hypot(c.x - b.cities[idx].center.x, c.z - b.cities[idx].center.z) < 6; },
    debug: state,
    dispose(){
      state.disposed = true; cancelAnimationFrame(raf); ro.disconnect();
      window.removeEventListener('keydown', kd); window.removeEventListener('keyup', ku);
      disposeGroup(scene); renderer.dispose(); el.remove();
    },
  };
}
