import Foundation
import Vision
import AppKit
var out:[[String:Any]]=[]
for path in CommandLine.arguments.dropFirst() {
 do {
  let request=VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.recognitionLanguages=["ko-KR","en-US"]
  request.usesLanguageCorrection=false
  let handler=VNImageRequestHandler(url: URL(fileURLWithPath:path),options:[:])
  try handler.perform([request])
  let rows=(request.results ?? []).compactMap { observation -> [String:Any]? in
   guard let text=observation.topCandidates(1).first else {return nil}
   let b=observation.boundingBox
   return ["text":text.string,"confidence":text.confidence,"x":b.minX,"y_top":1-b.maxY,"width":b.width,"height":b.height]
  }
  out.append(["path":path,"regions":rows])
 } catch {out.append(["path":path,"error":"\(error)"])}
}
let data=try JSONSerialization.data(withJSONObject:out,options:[.prettyPrinted,.sortedKeys])
FileHandle.standardOutput.write(data)
