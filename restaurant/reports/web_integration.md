# Web integration

`alchemist_web.glb` is the optimized delivery; `alchemist_web.blend` is its editable web copy. The reviewed high-quality source remains `alchemist_05_final.blend`.

- Actual GLB: 341,200 triangles, 55 meshes, 55 material primitives, 19.86 MB. Counts are asset counts, not a performance guarantee.
- glTF uses **Y up, meters**. Blender source is Z up. Let GLTFLoader apply the export axis conversion; do not add another X rotation. Keep the Restaurant root at unit scale for the authored 1.65 m pedestrian camera height.
- Hierarchy: Restaurant → Architecture, Dome, Tables, Seating, Lighting, Glassware, Props, InteractionTargets. Named cameras are CAM_Arrival, CAM_Hero, CAM_Dome, CAM_Table, CAM_Exit, and WALKTHROUGH. Static batches retain source object names in `userData.web_source_names` as a JSON string; the report contains the complete source-to-batch mapping and original mesh transforms.
- `Walkthrough_60s` animates the WALKTHROUGH camera for 60 seconds. Use an AnimationMixer on the loaded scene and render through that camera. Static camera choices do not require animation. Set perspective camera aspect and call updateProjectionMatrix on viewport changes.
- Interaction empties `entrance`, `hero_table`, `dome`, and `exit` retain `userData.interaction`. Get their world positions with getWorldPosition. Empties have no raycast surface: add application-owned invisible hit proxies or raycast the named door leaves, Counter_East5, and Dome_Projection. Navigation/collision logic and door-opening animation belong to the host application; this asset supplies spatial targets and the camera tour.
- Door leaves and sculptural reliefs, the hero counter/nearby setting, and projection dome remain separate. Other static surfaces are combined by category and material to reduce draw calls. The camera-guide curve PATH_Walkthrough and planning camera are excluded.
- Image base color, roughness, normal maps, transmission, clearcoat, sheen, and emission are retained in GLB. The stone roughness Multiply ×0.68 was resolved to a packed derived Non-Color image, rather than discarding its texture. The projection material is `PROJECTION | replace this image`; replace its emissiveMap for a different show while preserving its UV mapping.
- There are 16 shadowless punctual runtime lights. The selection retains one central dome bounce, all three centerline island pools, six representative table spots, two arrival lights, one portal light, one service light, and two street lights. Area lights have been approximated as points at half their source Blender wattage, except the island pools, which use twice the source wattage (8 W each) to preserve the warm centerline depth. Table spots retain the authored warm color and cone. All visible lamp meshes remain. Set `castShadow=false` after load. Tune intensity/exposure for the host renderer; Cycles light visibility flags and area shape are not supported by glTF punctual lights.
- **Interior environment required:** load `textures/restaurant_environment.exr` with EXRLoader and PMREMGenerator, and assign the PMREM texture to `scene.environment` while inside the restaurant. Do not set it as the background: the dome and architecture supply the visible room. On exit, restore the travel world's environment. The environment supplies broad interior reflection/ambient color, not spatially correct baked GI. Browser glass, contacts, reflections, and shadows will differ from the Cycles reference renders.
- The environment EXR is a separate integration artifact and is not embedded in GLB. No Draco decoder is required. glTF material extensions require a GLTFLoader version that supports the extensions listed in reports/web_export.json.

Three.js structure (equivalent R3F useGLTF/useFrame integration):

```js
const asset = await new GLTFLoader().loadAsync('/alchemist_web.glb');
scene.add(asset.scene);
asset.scene.traverse(o => { if (o.isLight) o.castShadow = false; });
const camera = asset.scene.getObjectByName('WALKTHROUGH');
const mixer = new THREE.AnimationMixer(asset.scene);
const clip = asset.animations.find(a => a.name === 'Walkthrough_60s') || asset.animations[0];
const action = mixer.clipAction(clip);
action.setLoop(THREE.LoopOnce, 1);
action.clampWhenFinished = true;
action.play();
const exr = await new EXRLoader().loadAsync('/textures/restaurant_environment.exr');
const pmrem = new THREE.PMREMGenerator(renderer);
const interiorEnvironment = pmrem.fromEquirectangular(exr).texture;
const exteriorEnvironment = scene.environment;
scene.environment = interiorEnvironment; // restore exteriorEnvironment on exit
// Each frame: mixer.update(deltaSeconds); renderer.render(scene, camera);
```

GLB structural validation is recorded in web_export.json. A separate loader/reimport validation and any browser performance measurements must be reported separately. No browser performance claim is made here.
