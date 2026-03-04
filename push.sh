#!/bin/bash
git -c credential.helper= -c credential.helper='!f() { echo "username=jwjo48"; echo "password=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"; }; f' push origin main
