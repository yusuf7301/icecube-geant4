#include "DetectorConstruction.hh"
#include "SensorSD.hh"
#include "Config.hh"

#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4MaterialPropertiesTable.hh"
#include "G4Box.hh"
#include "G4Orb.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4VisAttributes.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"

#include <cmath>
#include <fstream>

namespace
{
  // Dalga boyu aralığı: 300-600 nm (DOM fotokatodunun duyarlı olduğu bölge)
  const G4int    kNumOptPoints = 61;
  const G4double kLambdaMin = 300.;  // nm
  const G4double kLambdaMax = 600.;  // nm
  const G4double kHC = 1239.84193;   // eV*nm  (E[eV] = kHC / lambda[nm])

  // Derinliğe bağlı buz parametreleri (katman 0 = en derin / en alttaki).
  // 400 nm'deki toz soğurma uzunluğu ve Rayleigh saçılma uzunluğu.
  // Katman 2 "toz katmanı"nı temsil eder: daha çok soğurma ve saçılma.
  const G4double kAbs400[DetectorConstruction::kNumDOMs]  = {150., 110.,  45.,  90.}; // m
  const G4double kRay400[DetectorConstruction::kNumDOMs]  = { 45.,  35.,  12.,  28.}; // m

  const G4double kTopDepth = 2000.0*m;  // Buz bloğunun üst yüzeyinin nominal derinliği
}

DetectorConstruction::DetectorConstruction() : G4VUserDetectorConstruction() {}
DetectorConstruction::~DetectorConstruction() {}

G4double DetectorConstruction::IceHalfSize()   { return 10.0*m; }
G4double DetectorConstruction::WorldHalfSize() { return 15.0*m; }
G4double DetectorConstruction::SensorRadius()  { return 16.51*cm; } // Gerçek IceCube DOM'u: 33 cm çap

G4ThreeVector DetectorConstruction::SensorPosition(G4int id)
{
  // id = string*kNumDOMs + dom ;  string = ix*kNumStringsY + iy
  G4int dom = id % kNumDOMs;
  G4int str = id / kNumDOMs;
  G4int ix = str / kNumStringsY;
  G4int iy = str % kNumStringsY;
  G4double spacing = Config::Instance()->stringSpacing;
  G4double x = (ix - 1) * spacing;
  G4double y = (iy - 1) * spacing;
  G4double layerThickness = 2.*IceHalfSize() / kNumDOMs;
  G4double z = -IceHalfSize() + (dom + 0.5)*layerThickness; // Her DOM kendi katmanının ortasında
  return G4ThreeVector(x, y, z);
}

G4double DetectorConstruction::LayerDepth(G4int layer)
{
  G4double layerThickness = 2.*IceHalfSize() / kNumDOMs;
  G4double zc = -IceHalfSize() + (layer + 0.5)*layerThickness;
  return kTopDepth + (IceHalfSize() - zc); // z yukarı doğru, derinlik aşağı doğru artar
}

// Price & Bergström (1997) faz kırılma indisi (lambda mikron cinsinden), 400 nm'de ~1.32
G4double DetectorConstruction::IceRefractiveIndex(G4double lambda_nm)
{
  G4double l = lambda_nm / 1000.;
  return 1.55749 - 1.57988*l + 3.99993*l*l - 4.68271*l*l*l + 2.09354*l*l*l*l;
}

// Soğurma = toz bileşeni (lambda^-1.08) + buzun kendi kızılötesi soğurması
G4double DetectorConstruction::IceAbsLength(G4double lambda_nm, G4int layer)
{
  G4double aDust = (1./kAbs400[layer]) * std::pow(lambda_nm/400., -1.08); // 1/m
  G4double aIce  = 6954. * std::exp(-6700./lambda_nm);                    // 1/m
  return (1./(aDust + aIce)) * m;
}

// Rayleigh saçılması: uzunluk lambda^4 ile artar -> mavi ışık daha çok saçılır
G4double DetectorConstruction::IceRayleighLength(G4double lambda_nm, G4int layer)
{
  return kRay400[layer] * std::pow(lambda_nm/400., 4.) * m;
}

// Mie saçılması (Henyey-Greenstein, ileri yönlü). Etkin saçılma uzunluğu Rayleigh modelindekiyle
// aynı alınır ama dalga boyu bağımlılığı IceCube ölçümlerindeki gibi lambda^0.9'dur.
// Geant4'e verilen geometrik uzunluk = etkin uzunluk * (1 - <cos theta>).
G4double DetectorConstruction::IceMieLength(G4double lambda_nm, G4int layer)
{
  return kRay400[layer] * std::pow(lambda_nm/400., 0.9) * (1. - kMieG) * m;
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Material* vacuum = nist->FindOrBuildMaterial("G4_Galactic");
  G4Material* glass  = nist->FindOrBuildMaterial("G4_Pyrex_Glass");
  G4Material* water  = nist->FindOrBuildMaterial("G4_WATER");

  // Optik tablolar için foton enerjisi dizisi (artan enerji sırasında olmalı)
  std::vector<G4double> energies, lambdas;
  for (G4int i = 0; i < kNumOptPoints; ++i) {
    G4double lambda = kLambdaMax - i*(kLambdaMax - kLambdaMin)/(kNumOptPoints - 1);
    lambdas.push_back(lambda);
    energies.push_back(kHC/lambda * eV);
  }

  // 1. DÜNYA HACMİ: vakum. Fotonlar buzdan çıkınca burada soğurulur (RINDEX yok).
  G4double worldHalf = WorldHalfSize();
  auto* solidWorld = new G4Box("World", worldHalf, worldHalf, worldHalf);
  auto* logicWorld = new G4LogicalVolume(solidWorld, vacuum, "World");
  G4VPhysicalVolume* physWorld =
    new G4PVPlacement(nullptr, G4ThreeVector(), logicWorld, "World", nullptr, false, 0, true);
  logicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());

  // 2. SENSÖR (DOM): cam küre. Cama RINDEX verilir ki foton buzdan içeri girebilsin.
  auto* glassMPT = new G4MaterialPropertiesTable();
  std::vector<G4double> glassRindex(kNumOptPoints, 1.48);
  glassMPT->AddProperty("RINDEX", energies, glassRindex);
  glass->SetMaterialPropertiesTable(glassMPT);

  auto* solidSensor = new G4Orb("Sensor", SensorRadius());
  fLogicSensor = new G4LogicalVolume(solidSensor, glass, "Sensor");
  fLogicSensor->SetVisAttributes(G4VisAttributes(G4Colour(1.0, 0.8, 0.0)));

  // 3. BUZ KATMANLARI: her katman ayrı malzeme (aynı kırılma indisi, farklı soğurma/saçılma)
  G4double layerHalf = IceHalfSize() / kNumDOMs;
  auto* solidLayer = new G4Box("IceLayer", IceHalfSize(), IceHalfSize(), layerHalf);

  for (G4int layer = 0; layer < kNumDOMs; ++layer) {
    auto* ice = new G4Material("Ice_L" + std::to_string(layer), 0.917*g/cm3, water);

    std::vector<G4double> rindex, absLen, rayLen, mieLen;
    for (G4double lambda : lambdas) {
      rindex.push_back(IceRefractiveIndex(lambda));
      absLen.push_back(IceAbsLength(lambda, layer));
      rayLen.push_back(IceRayleighLength(lambda, layer));
      mieLen.push_back(IceMieLength(lambda, layer));
    }
    auto* mpt = new G4MaterialPropertiesTable();
    mpt->AddProperty("RINDEX",    energies, rindex);  // Dispersiyon -> Cherenkov
    mpt->AddProperty("ABSLENGTH", energies, absLen);  // Soğurma
    mpt->AddProperty("RAYLEIGH",  energies, rayLen);  // Rayleigh saçılması
    mpt->AddProperty("MIEHG",     energies, mieLen);  // Mie saçılması (makroda seçilir)
    mpt->AddConstProperty("MIEHG_FORWARD", kMieG);
    mpt->AddConstProperty("MIEHG_BACKWARD", kMieG);
    mpt->AddConstProperty("MIEHG_FORWARD_RATIO", 1.0);
    ice->SetMaterialPropertiesTable(mpt);

    auto* logicLayer = new G4LogicalVolume(solidLayer, ice, "IceLayer");
    G4double alpha = 0.15 + 0.1*layer;
    logicLayer->SetVisAttributes(G4VisAttributes(G4Colour(0.6, 0.85, 1.0, alpha)));

    G4double zc = -IceHalfSize() + (2*layer + 1)*layerHalf;
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, zc), logicLayer,
                      "IceLayer", logicWorld, false, layer, true);

    // Bu katmana ait DOM'ları (her string'de bir tane) yerleştir
    for (G4int str = 0; str < kNumStringsX*kNumStringsY; ++str) {
      G4int id = str*kNumDOMs + layer;
      G4ThreeVector pos = SensorPosition(id);
      new G4PVPlacement(nullptr, G4ThreeVector(pos.x(), pos.y(), pos.z() - zc),
                        fLogicSensor, "Sensor", logicLayer, false, id, true);
    }
  }

  return physWorld;
}

void DetectorConstruction::ConstructSDandField()
{
  auto* sd = new SensorSD("SensorSD");
  G4SDManager::GetSDMpointer()->AddNewDetector(sd);
  SetSensitiveDetector(fLogicSensor, sd);
}

void DetectorConstruction::WriteGeometryCSV(const G4String& prefix)
{
  std::ofstream sensors(prefix + "_sensors.csv");
  sensors << "sensor_id,string_id,dom_id,x_mm,y_mm,z_mm,radius_mm,depth_m\n";
  for (G4int id = 0; id < NumSensors(); ++id) {
    G4ThreeVector p = SensorPosition(id);
    sensors << id << ',' << id/kNumDOMs << ',' << id%kNumDOMs << ','
            << p.x()/mm << ',' << p.y()/mm << ',' << p.z()/mm << ','
            << SensorRadius()/mm << ',' << LayerDepth(id%kNumDOMs)/m << '\n';
  }

  std::ofstream ice(prefix + "_ice_properties.csv");
  ice << "layer,depth_m,zmin_mm,zmax_mm,wavelength_nm,n_phase,abs_length_m,rayleigh_length_m,mie_length_m\n";
  G4double layerThickness = 2.*IceHalfSize() / kNumDOMs;
  for (G4int layer = 0; layer < kNumDOMs; ++layer) {
    G4double zmin = -IceHalfSize() + layer*layerThickness;
    for (G4double lambda = kLambdaMin; lambda <= kLambdaMax + 0.1; lambda += 5.) {
      ice << layer << ',' << LayerDepth(layer)/m << ',' << zmin/mm << ','
          << (zmin + layerThickness)/mm << ',' << lambda << ','
          << IceRefractiveIndex(lambda) << ',' << IceAbsLength(lambda, layer)/m << ','
          << IceRayleighLength(lambda, layer)/m << ','
          << IceMieLength(lambda, layer)/m << '\n';
    }
  }
}
