#include "SensorSD.hh"
#include "OutputManager.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4OpticalPhoton.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

#include <iterator>

namespace
{
  // 10" fotoçoğaltıcı (bialkali katot + cam küre) için temsili kuantum verimi eğrisi
  const G4double kQELambda[] = {300., 320., 340., 360., 380., 400., 420., 450., 480., 500.,
                                530., 560., 600.};
  const G4double kQEValue[]  = {0.06, 0.15, 0.22, 0.25, 0.26, 0.255, 0.24, 0.21, 0.17, 0.14,
                                0.10, 0.065, 0.03};

  G4double QuantumEfficiency(G4double lambda_nm)
  {
    const G4int n = std::size(kQELambda);
    if (lambda_nm <= kQELambda[0] || lambda_nm >= kQELambda[n-1]) return 0.;
    G4int i = 1;
    while (kQELambda[i] < lambda_nm) ++i;
    G4double f = (lambda_nm - kQELambda[i-1]) / (kQELambda[i] - kQELambda[i-1]);
    return kQEValue[i-1] + f*(kQEValue[i] - kQEValue[i-1]);
  }
}

SensorSD::SensorSD(const G4String& name) : G4VSensitiveDetector(name) {}
SensorSD::~SensorSD() {}

G4bool SensorSD::ProcessHits(G4Step* step, G4TouchableHistory*)
{
  G4Track* track = step->GetTrack();
  if (track->GetDefinition() != G4OpticalPhoton::Definition()) return false;

  // Foton sensörde işini bitirdi: ister kaydedilsin ister edilmesin yok edilir
  track->SetTrackStatus(fStopAndKill);

  // Sadece dışarıdan (buzdan) giren fotonları say; cam içinde üretilenleri atla
  G4StepPoint* pre = step->GetPreStepPoint();
  if (pre->GetStepStatus() != fGeomBoundary) return false;

  // Kuantum verimi: foton fotoelektron üretir mi?
  G4double lambda = 1239.84193 / (pre->GetTotalEnergy()/eV);
  G4bool detected = G4UniformRand() < QuantumEfficiency(lambda);

  G4int sensorID = pre->GetTouchableHandle()->GetCopyNumber();
  OutputManager::Instance()->AddHit(sensorID, pre->GetPosition(), pre->GetTotalEnergy(),
                                    pre->GetGlobalTime(), track->GetParentID(), detected);
  return true;
}
