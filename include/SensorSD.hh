#ifndef SensorSD_h
#define SensorSD_h 1

#include "G4VSensitiveDetector.hh"

// Optik sensör (DOM): içine giren Cherenkov fotonunu "hit" olarak kaydeder ve yok eder.
class SensorSD : public G4VSensitiveDetector
{
  public:
    SensorSD(const G4String& name);
    virtual ~SensorSD();

    virtual G4bool ProcessHits(G4Step* step, G4TouchableHistory*);
};

#endif
