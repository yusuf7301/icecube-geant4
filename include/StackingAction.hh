#ifndef StackingAction_h
#define StackingAction_h 1

#include "G4UserStackingAction.hh"

class G4Track;

// Üretilen her Cherenkov fotonunu (konum, yön, enerji, zaman) yakalar.
class StackingAction : public G4UserStackingAction
{
  public:
    StackingAction();
    virtual ~StackingAction();

    virtual G4ClassificationOfNewTrack ClassifyNewTrack(const G4Track*);
};

#endif
