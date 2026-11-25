#ifndef OutputManager_h
#define OutputManager_h 1

#include "G4ThreeVector.hh"
#include "globals.hh"
#include <fstream>
#include <vector>

// Her thread'e ait CSV yazıcı + olay başına sayaçlar.
// Çok thread'li çalışmada her işçi kendi parça dosyasını yazar,
// koşu sonunda ana thread parçaları tek dosyada birleştirir (MergeParts).
class OutputManager
{
  public:
    static constexpr G4int kNumFiles = 5;

    static OutputManager* Instance(); // Thread'e özel örnek

    void Open(const G4String& prefix, G4int threadID); // threadID < 0 -> doğrudan son dosya
    void Close();
    static void MergeParts(const G4String& prefix);

    // --- Olay başı / sonu ---
    void BeginEvent(G4int eventID, G4bool savePhotons);
    void EndEvent(G4double E0, const G4ThreeVector& vertex, const G4ThreeVector& dir);

    // --- Kayıt fonksiyonları ---
    void AddPhoton(G4int parentID, const G4ThreeVector& pos, const G4ThreeVector& dir,
                   G4double energy, G4double time);
    void AddMuonStep(const G4ThreeVector& pos, G4double Epre, G4double Epost,
                     G4double edep, G4double stepLength, const G4String& process);
    void AddHit(G4int sensorID, const G4ThreeVector& pos, G4double energy,
                G4double time, G4int parentID, G4bool detected);
    void AddEdep(G4double edep) { fEdepTotal += edep; }
    void SetMuonExitEnergy(G4double e) { fMuonExitEnergy = e; }

  private:
    OutputManager() = default;

    std::ofstream fPhotons, fEloss, fHits, fEvents, fSummary;

    G4int    fEventID = 0;
    G4bool   fSavePhotons = false;
    G4bool   fSaveHitPhotons = true;
    G4bool   fSaveMuonSteps = true;
    G4long   fNPhotons = 0;
    G4long   fNPhotonsPrimary = 0;
    G4long   fNHits = 0;
    G4long   fNDetected = 0;     // Kuantum verimini geçen fotonlar
    G4int    fMuonStep = 0;
    G4double fMuonTrackLength = 0.;
    G4double fMuonDE = 0.;
    G4double fMuonDERad = 0.;    // Radyatif süreçlerle kaybedilen enerji
    G4double fMuonExitEnergy = -1.;
    G4double fEdepTotal = 0.;

    // Sensör başına olay özeti
    std::vector<G4long>   fSensorHits, fSensorDet;
    std::vector<G4double> fSensorTFirst, fSensorTFirstDet, fSensorTSum;
};

#endif
