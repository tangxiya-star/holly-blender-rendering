'use client';

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { Box, Move, RotateCcw, ZoomIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';

export default function DishViewer() {
  const mount = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [autoRotate, setAutoRotate] = useState(false);
  const readyRef = useRef(false);

  const reset = () => {
    cameraRef.current?.position.set(0, .225, .356);
    controlsRef.current?.target.set(0, .043, 0);
    controlsRef.current?.update();
    setAutoRotate(false);
  };

  useEffect(() => {
    if (controlsRef.current) controlsRef.current.autoRotate = autoRotate;
  }, [autoRotate]);

  useEffect(() => {
    type ModelContext = { registerTool: (tool: {
      name: string; description: string; inputSchema: object;
      annotations: { readOnlyHint: boolean; untrustedContentHint: boolean };
      execute: (input: unknown) => Promise<object>;
    }, options: { signal: AbortSignal }) => void | Promise<void> };
    const context = (document as Document & { modelContext?: ModelContext }).modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    try {
      void Promise.resolve(context.registerTool({
        name: 'reset_dish_view',
        description: 'Restore the dish viewer to its initial camera angle and stop automatic rotation.',
        inputSchema: { type: 'object', properties: {}, additionalProperties: false },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        async execute(input) {
          if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).length) throw new Error('Expected an empty object.');
          if (!readyRef.current || !cameraRef.current) throw new Error('The model is still loading.');
          reset();
          await new Promise<void>(resolve => requestAnimationFrame(() => resolve()));
          return { view: 'initial', autoRotate: false, camera: cameraRef.current?.position.toArray() };
        },
      }, { signal: lifecycle.signal })).catch(() => {});
    } catch { /* The visual controls remain available without WebMCP. */ }
    return () => lifecycle.abort();
  }, []);

  useEffect(() => {
    const host = mount.current;
    if (!host) return;
    let disposed = false;
    let model: THREE.Group | null = null;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    } catch {
      queueMicrotask(() => setError('浏览器暂时无法启动 3D 显示。请开启硬件加速后重试。'));
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.6));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.AgXToneMapping;
    renderer.toneMappingExposure = 1;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute('aria-label', '菜品三维模型：拖动旋转，滚轮或双指缩放，按 R 恢复视角');
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#101213');
    scene.fog = new THREE.Fog('#101213', .75, 1.7);
    const camera = new THREE.PerspectiveCamera(35, 1, .001, 10);
    camera.position.set(0, .225, .356);
    cameraRef.current = camera;
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, .043, 0);
    controls.enableDamping = true;
    controls.dampingFactor = .075;
    controls.minDistance = .13;
    controls.maxDistance = .72;
    controls.minPolarAngle = .12;
    controls.maxPolarAngle = Math.PI * .49;
    controls.autoRotateSpeed = .7;
    controls.zoomSpeed = .7;
    controls.panSpeed = .5;
    controls.listenToKeyEvents(renderer.domElement);
    controls.update();
    controlsRef.current = controls;

    const studio = new THREE.Scene();
    studio.background = new THREE.Color('#151515');
    const cards: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshBasicMaterial>[] = [];
    for (const [x, y, z, w, h, power] of [[-2, 3, 1, 3, 3, 5], [2, 1.2, 1, 2, 2, 1.5], [0, 2, -2, 2.5, 1.5, 2]]) {
      const card = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(power, power, power), side: THREE.DoubleSide }));
      card.position.set(x, y, z);
      card.lookAt(0, 0, 0);
      studio.add(card);
      cards.push(card);
    }
    const pmrem = new THREE.PMREMGenerator(renderer);
    const environment = pmrem.fromScene(studio, .07);
    scene.environment = environment.texture;
    scene.environmentIntensity = .38;

    const key = new THREE.SpotLight(0xfff3df, .8, 2, Math.PI / 3, .75, 2);
    key.position.set(-.24, .31, -.035);
    key.target.position.set(0, .04, 0);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = .05;
    key.shadow.camera.far = 1;
    key.shadow.bias = -.000005;
    key.shadow.normalBias = .00008;
    scene.add(key, key.target);
    const fill = new THREE.PointLight(0xd7e4ff, .085, 1, 2);
    fill.position.set(.10, .19, .30);
    scene.add(fill);

    const manager = new THREE.LoadingManager();
    manager.onProgress = (_, done, total) => {
      if (!disposed) setProgress(Math.min(96, Math.round(done / total * 96)));
    };
    const draco = new DRACOLoader(manager).setDecoderPath('/draco/').setWorkerLimit(2);
    const loader = new GLTFLoader(manager).setDRACOLoader(draco);
    const disposeModel = (group: THREE.Group) => group.traverse(object => {
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach(material => material.dispose());
      }
    });
    loader.load('/model/food_web.gltf', gltf => {
      if (disposed) { disposeModel(gltf.scene); return; }
      model = gltf.scene;
      model.traverse(object => {
        if (object instanceof THREE.Mesh) {
          object.castShadow = !object.name.toLowerCase().includes('tabletop');
          object.receiveShadow = true;
        }
      });
      scene.add(model);
      readyRef.current = true;
      setProgress(100);
      setLoaded(true);
    }, undefined, () => {
      if (!disposed) setError('模型加载未完成，请检查网络后重新加载。');
    });

    const resize = new ResizeObserver(() => {
      const { width, height } = host.getBoundingClientRect();
      if (!width || !height) return;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(35) / 2) / Math.min(1, camera.aspect)));
      camera.updateProjectionMatrix();
    });
    resize.observe(host);
    const keyboard = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === 'r') reset();
    };
    renderer.domElement.addEventListener('keydown', keyboard);
    renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

    return () => {
      disposed = true;
      readyRef.current = false;
      renderer.setAnimationLoop(null);
      resize.disconnect();
      controls.dispose();
      controlsRef.current = null;
      cameraRef.current = null;
      draco.dispose();
      if (model) disposeModel(model);
      environment.dispose();
      pmrem.dispose();
      cards.forEach(card => { card.geometry.dispose(); card.material.dispose(); });
      key.shadow.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return (
    <main className="viewer">
      <div ref={mount} className="canvas-mount" />
      <header className="viewer-header">
        <div className="identity">
          <div className="brand-mark"><Box size={22} strokeWidth={1.25} /></div>
          <div><p className="eyebrow">ALCHEMIST / STUDY 01</p><h1>菜品 <span>·</span> 3D 预览</h1></div>
        </div>
        <div className="live-label"><span className={loaded ? 'live-dot' : 'pending-dot'} />{loaded ? '实时模型' : '准备模型'}</div>
      </header>

      {!loaded && <div className="loading-overlay" aria-live="polite">
        <div className="loading-card">
          <Box className={error ? '' : 'loading-icon'} size={32} strokeWidth={1} />
          <h2>{error ? '暂时无法显示模型' : '正在准备你的菜品'}</h2>
          <p>{error || '首次打开需要加载完整的模型细节，请稍候。'}</p>
          {error ? <Button variant="outline" onClick={() => window.location.reload()}>重新加载</Button> : <Progress value={progress} aria-label="模型加载进度" className="loading-progress" />}
        </div>
      </div>}

      <footer className="viewer-footer">
        <div className="toolbar">
          <div className="gesture"><Move size={16} /><span className="desktop-hint">拖动旋转</span><span className="mobile-hint">单指旋转</span></div>
          <div className="gesture"><ZoomIn size={16} /><span className="desktop-hint">滚轮缩放</span><span className="mobile-hint">双指缩放</span></div>
          <span className="toolbar-divider" />
          <label className="rotate-toggle" htmlFor="auto-rotate"><Switch id="auto-rotate" checked={autoRotate} onCheckedChange={setAutoRotate} disabled={!loaded} />自动旋转</label>
          <Button variant="ghost" onClick={reset} disabled={!loaded} className="reset-button"><RotateCcw size={15} />恢复视角</Button>
        </div>
        <p className="material-note">网页实时材质与 Blender 的 Cycles 渲染会有差异。</p>
      </footer>
    </main>
  );
}
