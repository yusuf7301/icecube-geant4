#include "RunAction.hh"
#include "Config.hh"
#include "DetectorConstruction.hh"
#include "OutputManager.hh"

#include "G4Run.hh"
#include "G4Threading.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"

#include <filesystem>

RunAction::RunAction() : G4UserRunAction() {}
RunAction::~RunAction() {}

void RunAction::BeginOfRunAction(const G4Run*)
{
  Config* cfg = Config::Instance();
  fPrefix = cfg->prefix;
  G4bool mt = G4Threading::IsMultithreadedApplication();

  if (G4Threading::IsMasterThread()) {
    std::filesystem::path dir = std::filesystem::path(std::string(fPrefix)).parent_path();
    std::error_code ec;
    if (!dir.empty()) std::filesystem::create_directories(dir, ec);
    DetectorConstruction::WriteGeometryCSV(fPrefix);

    G4cout << "\n=== IceCube simulasyonu: " << cfg->particle << ", E = "
           << G4BestUnit(cfg->energy, "Energy") << ", kaynak RA = " << cfg->sourceRA/deg
           << " deg, Dec = " << cfg->sourceDec/deg << " deg"
           << "\n=== Cikti on eki: " << fPrefix << G4endl;
  }

  // Olayları işleyen thread (MT'de işçi, seri modda ana thread) dosyaları açar
  if (!mt)                                  OutputManager::Instance()->Open(fPrefix, -1);
  else if (!G4Threading::IsMasterThread()) OutputManager::Instance()->Open(fPrefix, G4Threading::G4GetThreadId());
}

void RunAction::EndOfRunAction(const G4Run* run)
{
  G4bool mt = G4Threading::IsMultithreadedApplication();

  if (!mt || !G4Threading::IsMasterThread()) OutputManager::Instance()->Close();

  // Ana thread, işçiler bittikten sonra çağrılır -> parçaları birleştir
  if (mt && G4Threading::IsMasterThread()) OutputManager::MergeParts(fPrefix);

  if (G4Threading::IsMasterThread())
    G4cout << "\n=== Koşu bitti: " << run->GetNumberOfEvent() << " olay -> "
           << fPrefix << "_*.csv" << G4endl;
}
