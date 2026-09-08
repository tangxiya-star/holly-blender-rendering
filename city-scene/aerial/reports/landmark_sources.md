# Copenhagen aerial landmark accents: sources and placement

These accents identify the city from aerial views. They are simplified roof and tower silhouettes, not surveyed reconstructions or detailed architectural assets. Existing mapped building footprints supply the lower masses. No landmark is relocated to improve a composition.

All local coordinates use origin **longitude 12.5683, latitude 55.6761**, with X east and Y north:

`X = (longitude - 12.5683) * 111320 * cos(55.6761 degrees)`

`Y = (latitude - 55.6761) * 111320`

Ground is Z = 2 m. Heights in the table are measured above that datum.

## Geographic evidence

The source is the project's downloaded `data/osm_raw.json` plus focused `data/landmark_parts_raw.json`, queried from OpenStreetMap through Overpass. Main data retrieval: **2026-09-08T20:21:34Z**, OSM base timestamp **2026-09-08T20:20:04Z**. Attribution: **© OpenStreetMap contributors**, [ODbL](https://www.openstreetmap.org/copyright).

The four principal tower/dome centers use the centroids of their actual mapped building parts. They do not use tourist-address pins or the centers of entire palace complexes. Coordinates below were calculated directly from those source geometries, with a stable polygon centroid calculation.

| Landmark | Actual source for accent center | Longitude | Latitude | Local X / Y, m | Height guide |
|---|---|---:|---:|---:|---|
| Frederik's Church / Marmorkirken | [OSM dome part 382667658](https://www.openstreetmap.org/way/382667658) | 12.58955083 | 55.68497182 | 1333.916 / 987.611 | 79 m overall; mapped main dome 36.6–53.9 m |
| Vor Frelsers Kirke | [OSM spire part 1012313938](https://www.openstreetmap.org/way/1012313938) | 12.59405732 | 55.67278630 | 1616.789 / -368.881 | 90 m |
| Christiansborg | [OSM tower part 381955936](https://www.openstreetmap.org/way/381955936) | 12.58040663 | 55.67622710 | 759.934 / 14.149 | 106 m |
| Copenhagen City Hall | [OSM tower part 1011067074](https://www.openstreetmap.org/way/1011067074) | 12.57050990 | 55.67558235 | 138.716 / -57.625 | 105.6 m |
| Rosenborg Castle | [OSM building 25524592](https://www.openstreetmap.org/way/25524592), with separately mapped turret parts | 12.57743642 | 55.68569083 | 573.494 / 1067.651 | Main turret 50.6 m; side turrets 36.2 m, OSM estimates |
| Copenhagen Opera House | [OSM building 1088494374](https://www.openstreetmap.org/way/1088494374) | 12.60074038 | 55.68198772 | 2036.285 / 655.421 | Approx. 38 m stage tower; 158 × 90 m roof |

The source distinguishes the Royal Opera House on Holmen from another small venue also named Operaen in Christiania. Only way 1088494374 receives the large canopy.

Rosenborg's three turret centers come from [part 383465284](https://www.openstreetmap.org/way/383465284), [part 383510582](https://www.openstreetmap.org/way/383510582), and [part 383510580](https://www.openstreetmap.org/way/383510580). Its main roof uses the orientation and dimensions of [part 383465248](https://www.openstreetmap.org/way/383465248), whose mapped roof begins at 13.8 m and ends at 20.4 m.

## Architectural evidence and simplification

- **Frederik's Church:** the Danish National Museum records its location and architectural identity in its [collection entry](https://samlinger.natmus.dk/dmr/asset/50270). The National Museum-authored [Lex architectural account](https://lex.dk/Frederikskirken) describes the 79 m copper dome/lantern and 30 m internal diameter. The model follows the OSM exterior dome diameter of approximately 35.9 m, with a short pale drum, ribbed green dome and narrow lantern. Individual columns and ribs are reduced to silhouette cues.
- **Our Saviour:** the official tourism organization describes the [external winding stair and 86 m visitor viewpoint](https://www.visitcopenhagen.com/copenhagen/planning/church-of-our-saviour-gdk410659). OSM maps the top at 90 m and the globe at 82.5–85 m. The model uses a dark copper taper, four golden spiral turns, globe and tiny summit figure cue. The [church's tower page](https://www.vorfrelserskirke.dk/taarn) is the source website linked on the mapped tower.
- **Christiansborg:** the [Royal Danish Collection](https://denkongeligesamling.dk/en/christiansborg-palace/interior-and-objects/the-tower-hall/) gives the 106 m height and describes the copper spire with three crowns. The accent abstracts that stepped copper profile and three gilt bands.
- **City Hall:** the [Danish Architecture Center](https://dac.dk/en/magazine/places/copenhagen-city-hall-details-at-towering-heights-36) documents Martin Nyrop's building and the asymmetrically placed 105.6 m tower. The accent uses its actual mapped tower center, red masonry shaft, open belfry and tapered copper crown.
- **Rosenborg:** the [Royal Danish Collection's building history](https://denkongeligesamling.dk/en/rosenborg-castle/) describes the third storey, spired oriel towers and large western tower. The three principal roof accents use the source positions and heights above. Spire curves are deliberately simplified.
- **Opera:** the [Royal Danish Theatre's architectural history](https://www.kglteater.dk/om-det-kongelige-teater/teatrets-historie/) documents the 158 m roof and 38 m stage tower. The [engineering software supplier's project case study](https://www.lusas.com/case/civil/copenhagen_opera_house.html) gives the 158 × 90 m canopy dimensions. Its orientation comes from the actual building outline; no façade or auditorium detailing is added.
- **Amalienborg:** the four matching palace buildings around the square are documented by [VisitCopenhagen](https://www.visitcopenhagen.com/copenhagen/planning/amalienborg-palace-gdk492887). Their actual mapped footprint IDs are **25524645, 106105298, 106105466 and 106228713**. They retain the mass builder's hipped roofs and sandstone palette; this module does not duplicate those masses with extra palace blocks.

## Mass integration

`landmark_building_override(id, tags, centroid)` returns a controlled eave height and whether to suppress the generic roof. Lower masses retain their OSM footprints. The Marble Church, Rosenborg and Opera get replacement roof silhouettes; the three tall civic/church accents rise through retained conventional roofs. Amalienborg's four source masses remain intact.

Eave heights are aerial modeling estimates except where explicitly supported by building-part height tags. They must not be confused with surveyed measurements. Christiansborg's large compound retains a simplified common eave; individual courtyard wings are not reconstructed. Total-height guides are strongest for the four documented major towers. Materials and profile segment sizes are authored approximations.

Runtime audit output is `reports/landmark_build_report.json`, including actual source coordinates, selected OSM tower parts, mesh counts and the mass override table.
