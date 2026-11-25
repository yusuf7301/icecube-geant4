#include "OutputManager.hh"
#include "Config.hh"
#include "DetectorConstruction.hh"
#include "G4SystemOfUnits.hh"

#include <filesystem>
#include <iomanip>
#include <limits>

namespace
{
  const G4double kHC = 1239.84193; // eV*nm

  // Dosya türleri ve başlık satırları
  const char* kNames[OutputManager::kNumFiles] = {
    "cherenkov_photons", "muon_energy_loss", "sensor_hits", "events", "sensor_summary"};
  const char* kHeaders[OutputManager::kNumFiles] = {
    "event,parent_id,x_mm,y_mm,z_mm,px,py,pz,energy_eV,wavelength_nm,time_ns",
    "event,step,x_mm,y_mm,z_mm,E_pre_MeV,E_post_MeV,dE_MeV,edep_MeV,step_mm,process",
    "event,sensor_id,string_id,dom_id,x_mm,y_mm,z_mm,energy_eV,wavelength_nm,time_ns,parent_id,detected",
    "event,E0_MeV,E_exit_MeV,E_loss_MeV,track_len_mm,edep_total_MeV,n_photons,"
    "n_photons_primary,n_hits,x0_mm,y0_mm,z0_mm,dir_x,dir_y,dir_z,n_detected,E_loss_rad_MeV",
    "event,sensor_id,string_id,dom_id,n_hits,n_detected,t_first_ns,t_first_det_ns,t_mean_ns"
  };

  G4String FileName(const G4String& prefix, G4int kind, G4int threadID)
  {
    G4String name = prefix + "_" + kNames[kind];
    if (threadID >= 0) name += ".part" + std::to_string(threadID);
    return name + ".csv";
  }

  // Radyatif (stokastik) müon süreçleri
  G4bool IsRadiative(const G4String& process)
  {
    return process == "muPairProd" || process == "muBrems" || process == "muonNuclear";
  }
}

OutputManager* OutputManager::Instance()
{
  static G4ThreadLocal OutputManager* instance = nullptr;
  if (!instance) instance = new OutputManager();
  return instance;
}

void OutputManager::Open(const G4String& prefix, G4int threadID)
{
  std::filesystem::path dir = std::filesystem::path(std::string(prefix)).parent_path();
  std::error_code ec;
  if (!dir.empty()) std::filesystem::create_directories(dir, ec);

  std::ofstream* files[kNumFiles] = {&fPhotons, &fEloss, &fHits, &fEvents, &fSummary};
  for (G4int k = 0; k < kNumFiles; ++k) {
    files[k]->open(FileName(prefix, k, threadID));
    *files[k] << kHeaders[k] << '\n';
    *files[k] << std::setprecision(7);
  }
}

void OutputManager::Close()
{
  fPhotons.close();
  fEloss.close();
  fHits.close();
  fEvents.close();
  fSummary.close();
}

void OutputManager::MergeParts(const G4String& prefix)
{
  for (G4int k = 0; k < kNumFiles; ++k) {
    std::ofstream out(FileName(prefix, k, -1));
    out << kHeaders[k] << '\n';
    for (G4int t = 0; t < 256; ++t) {
      G4String part = FileName(prefix, k, t);
      if (!std::filesystem::exists(std::string(part))) continue;
      {
        std::ifstream in(part);
        std::string header;
        std::getline(in, header);             // Başlık satırını atla
        if (in.peek() != EOF) out << in.rdbuf();
      }
      std::filesystem::remove(std::string(part));
    }
  }
}

void OutputManager::BeginEvent(G4int eventID, G4bool savePhotons)
{
  Config* cfg = Config::Instance();
  fEventID = eventID;
  fSavePhotons = savePhotons;
  fSaveHitPhotons = cfg->saveHitPhotons;
  fSaveMuonSteps = cfg->saveMuonSteps;
  fNPhotons = fNPhotonsPrimary = fNHits = fNDetected = 0;
  fMuonStep = 0;
  fMuonTrackLength = fMuonDE = fMuonDERad = fEdepTotal = 0.;
  fMuonExitEnergy = -1.;

  // Sensör başına özet sayaçları
  G4int n = DetectorConstruction::NumSensors();
  const G4double inf = std::numeric_limits<G4double>::max();
  fSensorHits.assign(n, 0);
  fSensorDet.assign(n, 0);
  fSensorTFirst.assign(n, inf);
  fSensorTFirstDet.assign(n, inf);
  fSensorTSum.assign(n, 0.);
}

void OutputManager::EndEvent(G4double E0, const G4ThreeVector& vertex, const G4ThreeVector& dir)
{
  // Müon buzdan çıkmadıysa (durdu/bozundu) çıkış enerjisi 0 kabul edilir
  G4double Eexit = (fMuonExitEnergy < 0.) ? 0. : fMuonExitEnergy;
  fEvents << fEventID << ',' << E0/MeV << ',' << Eexit/MeV << ',' << fMuonDE/MeV << ','
          << fMuonTrackLength/mm << ',' << fEdepTotal/MeV << ','
          << fNPhotons << ',' << fNPhotonsPrimary << ',' << fNHits << ','
          << vertex.x()/mm << ',' << vertex.y()/mm << ',' << vertex.z()/mm << ','
          << dir.x() << ',' << dir.y() << ',' << dir.z() << ','
          << fNDetected << ',' << fMuonDERad/MeV << '\n';

  // Sensör özeti: yalnızca en az bir foton alan sensörler (algılanmayan zaman = -1)
  for (std::size_t id = 0; id < fSensorHits.size(); ++id) {
    if (fSensorHits[id] == 0) continue;
    G4double tDet = fSensorDet[id] > 0 ? fSensorTFirstDet[id]/ns : -1.;
    fSummary << fEventID << ',' << id << ',' << id/DetectorConstruction::kNumDOMs << ','
             << id%DetectorConstruction::kNumDOMs << ',' << fSensorHits[id] << ','
             << fSensorDet[id] << ',' << fSensorTFirst[id]/ns << ',' << tDet << ','
             << fSensorTSum[id]/fSensorHits[id]/ns << '\n';
  }
}

void OutputManager::AddPhoton(G4int parentID, const G4ThreeVector& pos, const G4ThreeVector& dir,
                              G4double energy, G4double time)
{
  ++fNPhotons;
  if (parentID == 1) ++fNPhotonsPrimary;
  if (!fSavePhotons) return;

  G4double eV_ = energy/eV;
  fPhotons << fEventID << ',' << parentID << ','
           << std::setprecision(6) << pos.x()/mm << ',' << pos.y()/mm << ',' << pos.z()/mm << ','
           << std::setprecision(4) << dir.x() << ',' << dir.y() << ',' << dir.z() << ','
           << std::setprecision(5) << eV_ << ',' << kHC/eV_ << ','
           << std::setprecision(7) << time/ns << '\n';
}

void OutputManager::AddMuonStep(const G4ThreeVector& pos, G4double Epre, G4double Epost,
                                G4double edep, G4double stepLength, const G4String& process)
{
  fMuonTrackLength += stepLength;
  fMuonDE += Epre - Epost;
  if (IsRadiative(process)) fMuonDERad += Epre - Epost;
  if (!fSaveMuonSteps) { ++fMuonStep; return; }

  fEloss << fEventID << ',' << fMuonStep++ << ','
         << pos.x()/mm << ',' << pos.y()/mm << ',' << pos.z()/mm << ','
         << Epre/MeV << ',' << Epost/MeV << ',' << (Epre - Epost)/MeV << ','
         << edep/MeV << ',' << stepLength/mm << ',' << process << '\n';
}

void OutputManager::AddHit(G4int sensorID, const G4ThreeVector& pos, G4double energy,
                           G4double time, G4int parentID, G4bool detected)
{
  ++fNHits;
  ++fSensorHits[sensorID];
  fSensorTSum[sensorID] += time;
  if (time < fSensorTFirst[sensorID]) fSensorTFirst[sensorID] = time;
  if (detected) {
    ++fNDetected;
    ++fSensorDet[sensorID];
    if (time < fSensorTFirstDet[sensorID]) fSensorTFirstDet[sensorID] = time;
  }
  if (!fSaveHitPhotons) return;

  G4double eV_ = energy/eV;
  fHits << fEventID << ',' << sensorID << ',' << sensorID/DetectorConstruction::kNumDOMs << ','
        << sensorID%DetectorConstruction::kNumDOMs << ','
        << pos.x()/mm << ',' << pos.y()/mm << ',' << pos.z()/mm << ','
        << eV_ << ',' << kHC/eV_ << ',' << time/ns << ',' << parentID << ','
        << (detected ? 1 : 0) << '\n';
}
